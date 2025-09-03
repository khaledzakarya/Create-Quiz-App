import json
from langchain_ollama import OllamaLLM
from langchain.prompts import ChatPromptTemplate

# load your model
llm = OllamaLLM(model="gemma3:4b")

# define prompt once
prompt_template = ChatPromptTemplate.from_template("""
You are a strict but supportive tutor.
Grade the student's answer against the correct answer.

Question: {question}
Student Answer: {student_answer}
Correct Answer: {correct_answer}

Task:
1. Assign a score from 0–3 (0 = wrong, 1 = poor, 1.5 = weak partial,
   2 = fair partial, 2.5 = nearly correct, 3 = correct).
2. Write feedback in exactly this style:
   - Start with: "You did good in ..." listing strong points.
   - Then: "But weak topics you should focus on are ..." listing weak points.
   - Finally: "I suggest you practice ..." with 1–2 actionable advice tips.

Return JSON strictly in this format:
{{
  "score": X.X,
  "feedback": "You did good in ... But weak topics you should focus on are ... I suggest you practice ..."
}}
""")

def grade_answer(question: str, student_answer: str, correct_answer: str):
    """Grade a single answer using the LLM."""
    messages = prompt_template.format_messages(
        question=question,
        student_answer=student_answer,
        correct_answer=correct_answer
    )
    raw_output = llm.invoke(messages)

    # Try to parse JSON safely
    try:
        clean_output = raw_output.strip()
        if clean_output.startswith("```"):
            clean_output = clean_output.split("```json")[-1]
            clean_output = clean_output.split("```")[0]
        feedback_json = json.loads(clean_output)
    except Exception:
        feedback_json = {"score": None, "feedback": raw_output}

    return {
        "score": feedback_json.get("score"),
        "feedback": feedback_json.get("feedback")
    }
