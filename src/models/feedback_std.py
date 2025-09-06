import json
import re
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate

llm = OllamaLLM(model="gemma3:4b", temperature=0.7)


_AR_CHARS = re.compile(r"[\u0600-\u06FF]")
def is_arabic(s: str) -> bool:
    return bool(_AR_CHARS.search(s or ""))

# Two sets of rules: EN / AR
EN_RULES = """- If the answer is fully correct (TF/MCQ=1 or Written=3):
  - feedback = ONE short praise sentence (≤ 14 words), concept-specific.
  - praise_points = [concept]
  - weak_points = []
  - advice = ""
- If the answer is partially correct or incorrect:
  - feedback = EXACTLY THREE sentences:
      1. Lead-in (verbatim if provided)
      2. Must start with: "But weak topics you should focus on are ..."
         → include 1–2 short topics (≤ 12 words).
      3. Must start with: "I suggest you practice ..."
         → include ONE short actionable item (≤ 12 words).
  - praise_points = []
  - weak_points = [the topics you listed]
  - advice = the short action you gave"""

AR_RULES = """- إذا كانت الإجابة صحيحة بالكامل (صح/خطأ=1 أو مقالية=3):
  - feedback = جملة مدح قصيرة واحدة (≤ 14 كلمة) مرتبطة بالمفهوم.
  - praise_points = [المفهوم]
  - weak_points = []
  - advice = ""
- إذا كانت الإجابة غير صحيحة أو جزئية:
  - feedback = ثلاث جمل بالضبط:
      1. جملة lead-in كما هي.
      2. يجب أن تبدأ بـ: "لكن نقاط الضعف التي ينبغي التركيز عليها هي ..."
         → موضوع أو موضوعان قصيران (≤ 12 كلمة).
      3. يجب أن تبدأ بـ: "أنصحك أن تتدرّب على ..."
         → إجراء عملي واحد قصير (≤ 12 كلمة).
  - praise_points = []
  - weak_points = [الموضوعات المذكورة]
  - advice = الإجراء العملي المذكور"""


prompt_template = ChatPromptTemplate.from_template("""
You are a strict but supportive tutor.
Generate feedback ONLY in {lang}.

Question Type: {qtype}
Question: {question}
Student Answer: {student_answer}
Correct Answer: {correct_answer}
Given Score: {given_score}   # TF/MCQ: 0/1 ; Written: 0..3
Lead-in (if provided, must be the first sentence): {lead_in}

### Rules ({lang} only):
{rules}

Be concise. No extra context.

Return JSON ONLY:
{{
  "feedback": "...",
  "praise_points": [...],
  "weak_points": [...],
  "advice": "..."
}}
""")

def grade_answer(
    question: str,
    student_answer: str,
    correct_answer: str,
    qtype: str = "written",
    given_score: float | None = None,
    lead_in: str = "",
):
    # Decide language by detecting Arabic characters
    if is_arabic(question) or is_arabic(student_answer) or is_arabic(correct_answer):
        lang = "Arabic"
        rules = AR_RULES
    else:
        lang = "English"
        rules = EN_RULES

    messages = prompt_template.format_messages(
        lang=lang,
        rules=rules,
        qtype=qtype,
        question=question,
        student_answer=student_answer,
        correct_answer=correct_answer,
        given_score="None" if given_score is None else str(given_score),
        lead_in=lead_in or "None"
    )

    raw = llm.invoke(messages)

    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```json")[-1].split("```")[0]
        data = json.loads(clean)
    except Exception:
        data = {
            "feedback": raw,
            "praise_points": [],
            "weak_points": [],
            "advice": ""
        }

    return {
        "feedback": (data.get("feedback") or "").strip(),
        "praise_points": data.get("praise_points", []),
        "weak_points": data.get("weak_points", []),
        "advice": (data.get("advice") or "").strip(),
    }
