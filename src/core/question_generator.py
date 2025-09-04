import ollama, json, math
from models.quiz import Question, Quiz

class QuestionGenerator:
    def __init__(self, model: str = 'gemma3:4b'):
        self.model = model

    def _build_prompt(self, text, total_q, n_mcq, n_tf, n_written):
        return f"""
    You are an expert quiz generator.

    Task:
    - Create exactly {total_q} quiz questions from the provided text.
    - Distribution:
      • {n_mcq} Multiple Choice Questions (4 options)
      • {n_tf} True/False Questions
      • {n_written} Written Questions

    Output Rules:
    - STRICTLY return JSON, no extra text.
    - Structure must be:

    {{
      "quiz": [
        {{
          "type": "MCQ" | "TrueFalse" | "Written",
          "question": "<question text>",
          "options": ["...", "...", "...", "..."],   // only for MCQ, no A/B/C/D
          "answer": "<answer>"
        }}
      ]
    }}

    Notes:
    - True/False → "answer": "True" or "False"
    - Written → short model answer (1–3 sentences)
    - MCQ → provide 4 options, correct one must exactly match one of the "options"
    - Every question MUST have a valid "answer"
    - No explanation, no extra commentary, ONLY valid JSON.
    Text:
    ---
    {text}
    ---
    """


    def generate(self, text_chunks: list, n_questions: int,
                 mcq_ratio: float = 0.6, tf_ratio: float = 0.2,
                 written_ratio: float = 0.2):
        
        n_mcq = math.ceil(n_questions * mcq_ratio)
        n_tf = math.ceil(n_questions * tf_ratio)
        n_written = math.ceil(n_questions * written_ratio)
        total_q = n_mcq + n_tf + n_written

        all_questions = []
        for page in text_chunks:
            print(f"page content >>>>>>>>>{page}")
            prompt = self._build_prompt(page, total_q, n_mcq, n_tf, n_written)

            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"""
                        You are a structured quiz generator.
                        RULES:
                            1. You must generate EXACTLY {total_q} questions in total.
                            2. The distribution must be EXACTLY:
                            - {n_mcq} Multiple Choice Questions (MCQ)
                            - {n_tf} True/False Questions
                            - {n_written} Written Questions
                            3. Each question must strictly follow the JSON format provided.
                            4. Do not add explanations, notes, or greetings.
                            5. Do not skip or add fields in the JSON structure.
                            6. Every question MUST include a non-empty "answer" field:
                            - For MCQ: the correct option must be specified in "answer".
                            - For True/False: "answer" must be either "True" or "False".
                            - For Written: "answer" must contain a clear reference solution.
                            7. If you cannot follow the format, output exactly: ERROR: FORMAT VIOLATION.
                            8. If the number of questions, their distribution, or the presence of answers does not match the requirement, output exactly: ERROR: QUESTION COUNT VIOLATION.
                            9. Only output valid JSON. If invalid, output exactly: ERROR: JSON PARSE.
                            10. Do not add any id field
                    """},
                    {"role": "user", "content": prompt}
                ],
                format="json"
            )
            result = response['message']['content']

            # ✅ Handle errors
            if result.startswith("ERROR"):
                print(f"[ERROR from model] {result}")
                continue

            try:
                quiz_json = json.loads(result)
            except json.JSONDecodeError:
                print(f"[ERROR] Invalid JSON from model: {result}")
                continue

            for item in quiz_json.get("quiz", []):
                all_questions.append(
                    Question(
                        item.get("type"),
                        item.get("question"),
                        item.get("options", []),
                        item.get("answer", "")
                    )
                )

        return Quiz(all_questions)
