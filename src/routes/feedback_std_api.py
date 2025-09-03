from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

from src.models.feedback_std import grade_answer

# 👇 this must exist
app = FastAPI(title="Quiz Feedback API")

class QuizAnswer(BaseModel):
    question: str
    student_answer: str
    correct_answer: str
    type: str = "written"

@app.post("/feedback")
async def feedback(answers: List[QuizAnswer]):
    results = []
    for ans in answers:
        result = grade_answer(ans.question, ans.student_answer, ans.correct_answer)
        results.append(result)

    return {"results": results}
