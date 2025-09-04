from core.pdf_reader import PDFReader
from core.question_generator import QuestionGenerator
from core.question_selector import QuestionSelector
from typing import List, Optional

class QuizService:
    def __init__(self, pdf_path: str, model="gemma3:4b"):
        self.reader = PDFReader(pdf_path)
        self.generator = QuestionGenerator(model=model)
        self.selector = QuestionSelector()

    
    def _select_and_merge(self, focus_quiz, remain_quiz, q_type, n_focus, n_remain, f_ratio, r_ratio):
        focus_selected = self.selector.select_diverse(
            focus_quiz.filter_by_type(q_type),
            int(n_focus * f_ratio)
        )
        remain_selected = self.selector.select_diverse(
            remain_quiz.filter_by_type(q_type),
            int(n_remain * r_ratio)
        )

        final = focus_selected + remain_selected
        # for i, q in enumerate(final, start=1):
        #     q.id = i
        return final

    def generate_quiz(self, n_questions: Optional[int] = None,            
                    n_focus: int = None, n_remain: int = None,                           
                    focus_pages: Optional[List[int]] = None, remain_pages: Optional[List[int]] = None,
                    f_mcq_ratio: float = None,  f_tf_ratio: float = None, f_written_ratio: float = None,                
                    r_mcq_ratio: float = None, r_tf_ratio: float = None, r_written_ratio: float = None):

        pages = self.reader.extract_text_in_pages()

    
        if n_questions is not None and focus_pages is None and remain_pages is None:
            all_chunks = [p[1] for p in pages]

            quiz = self.generator.generate(all_chunks, n_questions,
                                        f_mcq_ratio, f_tf_ratio, f_written_ratio)

            Final_MCQ = self.selector.select_diverse(
                quiz.filter_by_type("MCQ"),
                int(n_questions * f_mcq_ratio)
            )
            # for i, q in enumerate(Final_MCQ, start=1):
            #     q.id = i

            Final_T_F = self.selector.select_diverse(
                quiz.filter_by_type("TrueFalse"),
                int(n_questions * f_tf_ratio)
            )
            # for i, q in enumerate(Final_T_F, start=1):
            #     q.id = i

            Final_Written = self.selector.select_diverse(
                quiz.filter_by_type("Written"),
                int(n_questions * f_written_ratio)
            )
            # for i, q in enumerate(Final_Written, start=1):
            #     q.id = i

            final_questions = [q.to_dict() for q in Final_MCQ] + [q.to_dict() for q in Final_T_F] + [q.to_dict() for q in Final_Written]
            return final_questions

        focus_chunks = [p[1] for p in pages if p[0] in focus_pages]
        remain_chunks = [p[1] for p in pages if p[0] in remain_pages]

        focus_quiz = self.generator.generate(focus_chunks, n_focus, f_mcq_ratio, f_tf_ratio, f_written_ratio)
        remain_quiz = self.generator.generate(remain_chunks, n_remain, r_mcq_ratio, r_tf_ratio, r_written_ratio)

        Final_MCQ = self._select_and_merge(focus_quiz, remain_quiz, "MCQ", n_focus, n_remain, f_mcq_ratio, r_mcq_ratio)
        Final_T_F = self._select_and_merge(focus_quiz, remain_quiz, "TrueFalse", n_focus, n_remain, f_tf_ratio, r_tf_ratio)
        Final_Written = self._select_and_merge(focus_quiz, remain_quiz, "Written", n_focus, n_remain, f_written_ratio, r_written_ratio)

        final_questions = [q.to_dict() for q in Final_MCQ] + [q.to_dict() for q in Final_T_F] + [q.to_dict() for q in Final_Written]
        return final_questions

