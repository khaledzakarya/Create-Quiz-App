from services.quiz_service import QuizService

if __name__ == "__main__":
    pdf_path = "data\The Machine Learning Pipeline.pdf"
    service = QuizService(pdf_path)

    quiz = service.generate_quiz(
        focus_pages=[2, 3],
        remain_pages=[1, 4, 5],
        n_focus=40,
        n_remain=20,
        f_mcq_ratio=0.6,
        f_tf_ratio=0.2,
        f_written_ratio=0.2,
        r_mcq_ratio=0.6,
        r_tf_ratio=0.2,
        r_written_ratio=0.2
    )

    print(quiz)
