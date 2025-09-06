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
    type: str = "written"        # "mcq" | "tf" | "written" or Arabic equivalents
    score: Optional[float] = None

# Arabic script detection
_AR_CHARS = re.compile(r"[\u0600-\u06FF]")
def is_arabic(s: str) -> bool:
    return bool(_AR_CHARS.search(s or ""))

def _norm(s: str) -> str:
    return (s or "").strip().lower()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/feedback")
async def feedback(answers: List[QuizAnswer]):
    results: List[Dict] = []
    weak_pool: List[str] = []
    positive_pool: List[str] = []

    # If ANY Arabic in questions → summary in Arabic
    ar_mode = any(is_arabic(a.question) for a in answers)

    # Normalize TF answers
    tf_map = {
        "true":"true","t":"true","1":"true","yes":"true",
        "false":"false","f":"false","0":"false","no":"false",
        "صحيح":"true","صح":"true","نعم":"true","ايوه":"true","أيوا":"true",
        "خطأ":"false","غلط":"false","لا":"false"
    }

    # Normalize type labels (English/Arabic)
    type_map = {
        "صح/خطأ": "tf",
        "اختيار من متعدد": "mcq",
        "اختيارات متعددة": "mcq",
        "إجابة كتابية": "written",
        "مقالية": "written"
    }

    for a in answers:
        item_ar = is_arabic(a.question) or is_arabic(a.student_answer) or is_arabic(a.correct_answer)
        atype = type_map.get(a.type.strip(), a.type.strip())

        fully_correct = False
        lead_in = ""

        if atype in ("mcq", "tf"):
            sa = _norm(a.student_answer)
            ca = _norm(a.correct_answer)
            if atype == "tf":
                sa = tf_map.get(sa, sa)
                ca = tf_map.get(ca, ca)
            if a.score == 1 and sa and ca and sa == ca:
                fully_correct = True
            else:
                lead_in = "إجابتك غير صحيحة." if item_ar else "Your answer is incorrect."

        elif atype == "written":
            if a.score == 3:
                fully_correct = True
            elif a.score == 0:
                lead_in = "إجابتك غير صحيحة." if item_ar else "Your answer is incorrect."
            else:
                lead_in = "إجابتك غير دقيقة." if item_ar else "Your answer is not fully accurate."

        # --- call LLM ---
        out = grade_answer(
            question=a.question,
            student_answer=a.student_answer,
            correct_answer=a.correct_answer,
            qtype=atype,
            given_score=a.score,
            lead_in=lead_in if not fully_correct else ""
        )

        results.append({
            "student_id": a.student_id,
            "quiz_id": a.quiz_id,
            "question": a.question,
            "student_answer": a.student_answer,
            "correct_answer": a.correct_answer,
            "type": atype,
            "score": a.score,
            "feedback": out["feedback"]
        })

        positive_pool += out.get("praise_points", [])
        weak_pool += out.get("weak_points", [])

    # --- summary ---
    def _dedupe(xs):
        seen, out = set(), []
        for x in xs:
            sx = (x or "").strip()
            if sx and sx not in seen:
                seen.add(sx)
                out.append(sx)
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
