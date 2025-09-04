import ollama, json, math
from models.quiz import Question, Quiz

class QuestionGenerator:
    def __init__(self, model: str = 'gemma3:4b'):
        self.model = model

    def _build_prompt(self, text, total_q, n_mcq, n_tf, n_written):
        return f"""
        You are an expert quiz generator.

        IMPORTANT RULES:
        - You MUST generate questions STRICTLY from the provided text.
        - Do NOT invent questions outside the text.
        - If the text does not contain enough information, return exactly: ERROR: INSUFFICIENT DATA.

        Task:
        - Create exactly {total_q} quiz questions.
        - Distribution:
          • {n_mcq} Multiple Choice Questions (MCQ)
          • {n_tf} True/False Questions
          • {n_written} Written Questions

        Output Rules:
        - STRICTLY return JSON, no extra text.
        - Structure must be:

        {{
          "quiz": [
            {{
              "id": <number>,
              "type": "MCQ" | "TrueFalse" | "Written",
              "question": "<question text>",
              "options": ["A) ...", "B) ...", "C) ...", "D) ..."],   // only for MCQ
              "answer": "<answer>"
            }}
          ]
        }}

        Notes:
        - True/False → "answer": "True" or "False"
        - Written → short model answer (1–3 sentences)
        - MCQ → 4 options, one must be correct (matching "answer")

        Text to use (do NOT go beyond this):
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
            print(f"\n[DEBUG] Page Content >>>>>>\n{page}\n")

            prompt = self._build_prompt(page, total_q, n_mcq, n_tf, n_written)

            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"""
                        You are a structured quiz generator.
                        RULES:
                        1. Generate ONLY from the given text.
                        2. Exactly {total_q} questions.
                           - {n_mcq} MCQ
                           - {n_tf} True/False
                           - {n_written} Written
                        3. IDs start at 1 and increment by 1.
                        4. JSON ONLY, no explanations, no notes.
                        5. If invalid JSON → output: ERROR: JSON PARSE.
                        6. If count wrong → output: ERROR: QUESTION COUNT VIOLATION.
                        7. If nothing relevant in text → output: ERROR: INSUFFICIENT DATA.
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
                        item.get("id"),
                        item.get("type"),
                        item.get("question"),
                        item.get("options", []),
                        item.get("answer", "")
                    )
                )

        return Quiz(all_questions)
