from core.pdf_reader import PDFReader
from core.question_generator import QuestionGenerator
from core.question_selector import QuestionSelector

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
        for i, q in enumerate(final, start=1):
            q.id = i
        return final

    def generate_quiz(self, focus_pages, remain_pages,
                    n_focus=10, n_remain=5,
                    f_mcq_ratio=0.6, f_tf_ratio=0.2, f_written_ratio=0.2,
                    r_mcq_ratio=0.6, r_tf_ratio=0.2, r_written_ratio=0.2):

        pages = self.reader.extract_text_in_pages()
        focus_chunks = [p[1] for p in pages if p[0] in focus_pages]
        remain_chunks = [p[1] for p in pages if p[0] in remain_pages]

        focus_quiz = self.generator.generate(focus_chunks, n_focus, f_mcq_ratio, f_tf_ratio, f_written_ratio)
        remain_quiz = self.generator.generate(remain_chunks, n_remain, r_mcq_ratio, r_tf_ratio, r_written_ratio)

        Final_MCQ = self._select_and_merge(focus_quiz, remain_quiz, "MCQ", n_focus, n_remain, f_mcq_ratio, r_mcq_ratio)
        Final_T_F = self._select_and_merge(focus_quiz, remain_quiz, "TrueFalse", n_focus, n_remain, f_tf_ratio, r_tf_ratio)
        Final_Written = self._select_and_merge(focus_quiz, remain_quiz, "Written", n_focus, n_remain, f_written_ratio, r_written_ratio)

        return {
            "MCQ": [q.to_dict() for q in Final_MCQ],
            "TrueFalse": [q.to_dict() for q in Final_T_F],
            "Written": [q.to_dict() for q in Final_Written],
        }

