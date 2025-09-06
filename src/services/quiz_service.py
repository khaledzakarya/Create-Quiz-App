from controller import PDFReader
from controller import QuestionGenerator
from controller import QuestionSelector
from models.enums import QuestionTypeEnum
from typing import List, Optional
from helpers.config import get_settings

class QuizService:
    def __init__(self, pdf_path: str, model: Optional[str] = None):
        settings = get_settings()
        model_name = model or settings.QUIZ_GENERATION_MODEL

        self.reader = PDFReader(pdf_path)
        self.generator = QuestionGenerator(model=model_name)
        self.selector = QuestionSelector()

    
    def _select_and_merge(self, focus_quiz, remain_quiz, q_type, n_focus, n_remain, f_ratio, r_ratio):
        focus_selected = self.selector.select_diverse(
            questions=focus_quiz.filter_by_type(q_type),
            k=int(n_focus * f_ratio)
        )
        remain_selected = self.selector.select_diverse(
            questions=remain_quiz.filter_by_type(q_type),
            k=int(n_remain * r_ratio)
        )

        final = focus_selected + remain_selected

        return final

    def generate_quiz(self, level: str, n_questions: Optional[int] = None,            
                    n_focus: int = None, n_remain: int = None,                           
                    focus_pages: Optional[List[int]] = None, remain_pages: Optional[List[int]] = None,
                    f_mcq_ratio: float = None,  f_tf_ratio: float = None, f_written_ratio: float = None,                
                    r_mcq_ratio: float = None, r_tf_ratio: float = None, r_written_ratio: float = None):

        pages = self.reader.extract_text_in_pages()

    
        if n_questions is not None and focus_pages is None and remain_pages is None:
            all_chunks = [p[1] for p in pages]

            quiz = self.generator.generate(
                level=level, text_chunks=all_chunks, 
                n_questions=n_questions,
                mcq_ratio=f_mcq_ratio, tf_ratio=f_tf_ratio, written_ratio=f_written_ratio
            )

            Final_MCQ = self.selector.select_diverse(
                questions=quiz.filter_by_type(QuestionTypeEnum.MCQ.value),
                k=int(n_questions * f_mcq_ratio)
            )

            Final_T_F = self.selector.select_diverse(
                questions=quiz.filter_by_type(QuestionTypeEnum.TRUEFALSE.value),
                k=int(n_questions * f_tf_ratio)
            )

            Final_Written = self.selector.select_diverse(
                questions=quiz.filter_by_type(QuestionTypeEnum.WRITTEN.value),
                k=int(n_questions * f_written_ratio)
            )


            final_questions = [q.to_dict() for q in Final_MCQ] + [q.to_dict() for q in Final_T_F] + [q.to_dict() for q in Final_Written]
            return final_questions

        focus_chunks = [p[1] for p in pages if p[0] in focus_pages]
        remain_chunks = [p[1] for p in pages if p[0] in remain_pages]

        focus_quiz = self.generator.generate(
            level=level, text_chunks=focus_chunks, 
            n_questions=n_focus, 
            mcq_ratio=f_mcq_ratio, tf_ratio=f_tf_ratio, written_ratio=f_written_ratio
        )

        remain_quiz = self.generator.generate(
            level=level, text_chunks=remain_chunks, 
            n_questions=n_remain, 
            mcq_ratio=r_mcq_ratio, tf_ratio=r_tf_ratio, written_ratio=r_written_ratio
        )

        Final_MCQ = self._select_and_merge(
            focus_quiz=focus_quiz, remain_quiz=remain_quiz, 
            q_type=QuestionTypeEnum.MCQ.value, 
            n_focus=n_focus, n_remain=n_remain, 
            f_ratio=f_mcq_ratio, r_ratio=r_mcq_ratio
        )
        
        Final_T_F = self._select_and_merge(
            focus_quiz=focus_quiz, remain_quiz=remain_quiz, 
            q_type=QuestionTypeEnum.TRUEFALSE.value, 
            n_focus=n_focus, n_remain=n_remain,
            f_ratio=f_tf_ratio, r_ratio=r_tf_ratio
        )

        Final_Written = self._select_and_merge(
            focus_quiz=focus_quiz, remain_quiz=remain_quiz, 
            q_type=QuestionTypeEnum.WRITTEN.value, 
            n_focus=n_focus, n_remain=n_remain, 
            f_ratio=f_written_ratio, r_ratio=r_written_ratio
        )

        final_questions = [q.to_dict() for q in Final_MCQ] + [q.to_dict() for q in Final_T_F] + [q.to_dict() for q in Final_Written]
        return final_questions

