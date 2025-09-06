from fastapi import FastAPI , APIRouter
from .schema import QuizRequest
from stores.llm.quiz_service import QuizService

generate_router = APIRouter(
    prefix = "/ai/generate_quiz",
    tags = ["ai"]
)


@generate_router.post("/")
async def generate_quizes(request : QuizRequest):
    service = QuizService(pdf_path=request.pdf_path, language=request.language)
    quiz = service.generate_quiz(
        level=request.level,
        n_questions=request.n_questions,
        focus_pages=request.focus_pages,
        remain_pages=request.remain_pages,
        n_focus=request.n_focus,
        n_remain=request.n_remain,
        f_mcq_ratio=request.f_mcq_ratio,
        f_tf_ratio=request.f_tf_ratio,
        f_written_ratio=request.f_written_ratio,
        r_mcq_ratio=request.r_mcq_ratio,
        r_tf_ratio=request.r_tf_ratio,
        r_written_ratio=request.r_written_ratio
        )
    return quiz