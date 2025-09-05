from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict
import re

from src.models.feedback_std import grade_answer

app = FastAPI(title="Quiz Feedback API")

class QuizAnswer(BaseModel):
    student_id: Optional[str] = None
    quiz_id: Optional[str] = None
    question: str
    student_answer: str
    correct_answer: str
    type: str = "written"        # "mcq" | "tf" | "written"
    score: Optional[float] = None  # PROVIDED BY CLIENT

# ---------- Language helpers ----------
_AR_CHARS = re.compile(r"[\u0600-\u06FF]")  # Arabic script range

def is_arabic(s: str) -> bool:
    return bool(_AR_CHARS.search(s or ""))

def _norm(s: str) -> str:
    return (s or "").strip().lower()

# ---------- Extractors (EN & AR variants) ----------
_WEAK_RE_EN = re.compile(
    r"But weak topics you should focus on are\s+(.*?)(?:\s*I suggest|\s*$)",
    flags=re.IGNORECASE | re.DOTALL
)
_GOOD_RE_EN = re.compile(
    r"You did good in\s+(.*?)(?:\.\s|But weak topics|$)",
    flags=re.IGNORECASE | re.DOTALL
)

_WEAK_RE_AR = re.compile(
    r"لكن نقاط الضعف التي ينبغي التركيز عليها هي\s+(.*?)(?:\s*أنصحك|$)",
    flags=re.IGNORECASE | re.DOTALL
)
_GOOD_RE_AR = re.compile(
    r"أحسنت في\s+(.*?)(?:\.\s|لكن نقاط الضعف|$)",
    flags=re.IGNORECASE | re.DOTALL
)

def _sanitize_topic(t: str) -> Optional[str]:
    t = (t or "").strip(" .،,:;|-_")
    if len(t) < 3 or len(t) > 40:
        return None
    if re.fullmatch(r"[^\w\u0600-\u06FF]+", t or ""):
        return None
    return t

def _split_topics(frag: str) -> List[str]:
    parts = re.split(r",|،|\band\b|و", frag, flags=re.IGNORECASE)
    seen, out = set(), []
    for p in parts:
        t = (p or "").strip()
        st = _sanitize_topic(t)
        if st and st not in seen:
            seen.add(st); out.append(st)
        if len(out) >= 3:
            break
    return out

def extract_weak_points(feedback: str, ar: bool) -> List[str]:
    m = (_WEAK_RE_AR if ar else _WEAK_RE_EN).search(feedback or "")
    return _split_topics(m.group(1)) if m else []

def extract_good_points(feedback: str, ar: bool) -> List[str]:
    m = (_GOOD_RE_AR if ar else _GOOD_RE_EN).search(feedback or "")
    return _split_topics(m.group(1)) if m else []

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/feedback")
async def feedback(answers: List[QuizAnswer]):
    results: List[Dict] = []
    weak_pool: List[str] = []
    positive_pool: List[str] = []

    # Decide summary language: if ANY Arabic in questions, go Arabic
    ar_mode = any(is_arabic(a.question) for a in answers)

    # Combined TF normalization (EN + AR)
    tf_map = {
        "true":"true","t":"true","1":"true","yes":"true",
        "false":"false","f":"false","0":"false","no":"false",
        "صحيح":"true","صح":"true","نعم":"true","ايوه":"true","أيوا":"true",
        "خطأ":"false","غلط":"false","لا":"false"
    }

    for a in answers:
        item_ar = is_arabic(a.question) or is_arabic(a.student_answer) or is_arabic(a.correct_answer)

        # --- fully-correct detection by score & type ---
        fully_correct = False
        lead_in = ""

        if a.type in ("mcq", "tf"):
            sa = _norm(a.student_answer); ca = _norm(a.correct_answer)
            if a.type == "tf":
                sa = tf_map.get(sa, sa); ca = tf_map.get(ca, ca)
            fully_correct = bool(sa and sa == ca and a.score == 1)
            if not fully_correct:
                lead_in = "إجابتك غير صحيحة." if item_ar else "Your answer is incorrect."
        else:  # written: 0..3
            if a.score == 3:
                fully_correct = True
            elif a.score == 0:
                lead_in = "إجابتك غير صحيحة." if item_ar else "Your answer is incorrect."
            else:  # 1 or 2
                lead_in = "إجابتك غير دقيقة." if item_ar else "Your answer is not fully accurate."

        # --- call LLM ---
        if fully_correct:
            out = grade_answer(
                question=a.question,
                student_answer=a.student_answer,
                correct_answer=a.correct_answer,
                qtype=a.type,
                given_score= a.score if a.score is not None else (1 if a.type in ("mcq","tf") else 3),
                lead_in=""  # ignored in praise-mode
            )
            results.append({
                "student_id": a.student_id,
                "quiz_id": a.quiz_id,
                "question": a.question,
                "student_answer": a.student_answer,
                "correct_answer": a.correct_answer,
                "type": a.type,
                "score": a.score,
                "feedback": out["feedback"]
            })
            positive_pool += (["أسئلة صح/خطأ"] if (item_ar and a.type=="tf") else
                              ["true/false facts"] if a.type=="tf" else
                              (["اختيارات متعددة"] if item_ar else ["multiple-choice accuracy"]))
        else:
            out = grade_answer(
                question=a.question,
                student_answer=a.student_answer,
                correct_answer=a.correct_answer,
                qtype=a.type,
                given_score=a.score if a.score is not None else None,
                lead_in=lead_in
            )
            results.append({
                "student_id": a.student_id,
                "quiz_id": a.quiz_id,
                "question": a.question,
                "student_answer": a.student_answer,
                "correct_answer": a.correct_answer,
                "type": a.type,
                "score": a.score,
                "feedback": out["feedback"]
            })
            weak_pool += extract_weak_points(out.get("feedback", ""), item_ar)
            positive_pool += extract_good_points(out.get("feedback", ""), item_ar)

    # --- summary (dedupe + sanitize) ---
    def _dedupe(xs):
        seen, out = set(), []
        for x in xs:
            sx = _sanitize_topic(x)
            if sx and sx not in seen:
                seen.add(sx); out.append(sx)
        return out

    pos = _dedupe(positive_pool)[:2]
    neg = _dedupe(weak_pool)[:3]

    if ar_mode:
        if neg:
            summary = (
                (f"عمل جيد—أحسنت في {', '.join(pos)}. " if pos else "مجهود طيب. ")
                + f"ولتحسين مستواك، ركّز على {', '.join(neg)}."
            )
        else:
            summary = "عمل ممتاز إجمالًا—استمر!"
    else:
        if neg:
            summary = (
                (f"Nice work—you did good in {', '.join(pos)}. " if pos else "Good effort. ")
                + f"To improve, focus on {', '.join(neg)}."
            )
        else:
            summary = "Excellent work overall—keep it up!"

    return {"results": results, "summary_feedback": summary}
