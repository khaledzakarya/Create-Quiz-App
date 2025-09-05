# feedback_std.py
import json
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate

llm = OllamaLLM(model="gemma3:4b", temperature=0.7)

prompt_template = ChatPromptTemplate.from_template("""
You are a strict but supportive tutor.
Generate FEEDBACK ONLY in the SAME LANGUAGE as the Question.

Question Type: {qtype}
Question: {question}
Student Answer: {student_answer}
Correct Answer: {correct_answer}
Given Score: {given_score}   # TF/MCQ: 0/1 ; Written: 0..3
Lead-in (first sentence, must use verbatim if provided): {lead_in}

Rules:
- If Given Score indicates a fully correct answer (TF/MCQ=1 or Written=3):
    - Return EXACTLY ONE short praise sentence (≤ 14 words), specific to the concept.
- If (Question Type in ["mcq","tf"] and Given Score == 1) OR (Question Type=="written" and Given Score==3):
  - Return EXACTLY ONE short praise sentence (≤ 14 words), specific to the concept.
  - No advice, no extra clauses.

- If (Question Type in ["mcq","tf"] and Given Score == 0) OR (Question Type=="written" and Given Score<3):
  - Use EXACTLY THREE sentences TOTAL.
  - The FIRST sentence MUST be EXACTLY the Lead-in provided above.
  - The SECOND sentence MUST start with (same language):
    EN: "But weak topics you should focus on are ..." (1–2 short topics, ≤ 12 words)
    AR: "لكن نقاط الضعف التي ينبغي التركيز عليها هي ..." (موضوع أو موضوعان قصيران ≤ 12 كلمة)
  - The THIRD sentence MUST start with:
    EN: "I suggest you practice ..." (ONE short actionable item, ≤ 12 words)
    AR: "أنصحك أن تتدرّب على ..." (إجراء عملي واحد ≤ 12 كلمة)


- Otherwise (partial or incorrect):
  - Use EXACTLY THREE sentences TOTAL.
  - The FIRST sentence MUST be EXACTLY the Lead-in provided above.
  - The SECOND sentence MUST start with (same language):
    EN: "But weak topics you should focus on are ..." (1–2 short topics, ≤ 12 words)
    AR: "لكن نقاط الضعف التي ينبغي التركيز عليها هي ..." (موضوع أو موضوعان قصيران ≤ 12 كلمة)
  - The THIRD sentence MUST start with:
    EN: "I suggest you practice ..." (ONE short actionable item, ≤ 12 words)
    AR: "أنصحك أن تتدرّب على ..." (إجراء عملي واحد ≤ 12 كلمة)

Be concise. No extra context.

Return JSON ONLY:
{{
  "feedback": "..."
}}
""")

def grade_answer(
    question: str,
    student_answer: str,
    correct_answer: str,
    qtype: str = "written",
    given_score: float | None = None,
    lead_in: str = "",   # NEW: enforce the first sentence when not fully correct
):
    messages = prompt_template.format_messages(
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
        data = {"feedback": raw}
    return {"feedback": (data.get("feedback") or "").strip()}
