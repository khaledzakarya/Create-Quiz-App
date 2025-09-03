import ollama, json, math
from models.quiz import Question, Quiz

class QuestionGenerator:
    def __init__(self, model: str = 'gemma3:4b'):
        self.model = model

    def generate(self, text_chunks: list, n_questions: int,
                mcq_ratio: float = 0.6, tf_ratio: float = 0.2,
                written_ratio: float = 0.2):
        
        n_mcq = math.ceil(n_questions * mcq_ratio)
        n_tf = math.ceil(n_questions * tf_ratio)
        n_written = math.ceil(n_questions * written_ratio)

        total_q = n_mcq + n_tf + n_written

        all_questions = []
        for page in text_chunks:
            prompt = self._build_prompt(page, total_q, n_mcq,
                                       n_tf, n_written)
            
            response = ollama.chat(
                model = self.model,
                messages = [
                            {"role": "system", "content": f'''You are a structured quiz generator.
                                                            RULES:
                                                            1. You must generate EXACTLY {total_q} questions in total.
                                                            2. The distribution must be EXACTLY:
                                                                - {n_mcq} Multiple Choice Questions (MCQ)
                                                                - {n_tf} True/False Questions
                                                                - {n_written} Written Questions
                                                            3. Each question must strictly follow the JSON format provided.
                                                            4. IDs must start from 1 and increment by 1 without skipping.
                                                            5. Do not add explanations, notes, or greetings.
                                                            6. Do not skip or add fields in the JSON structure.
                                                            7. If you cannot follow the format, output exactly: ERROR: FORMAT VIOLATION.
                                                            8. If the number of questions or their distribution does not match the requirement, output exactly: ERROR: QUESTION COUNT VIOLATION.
                                                            9. Only output valid JSON. If invalid, output exactly: ERROR: JSON PARSE.
                                                            '''},
                            {"role": "user", "content": prompt}
                ],
                format = 'json'
            )

            quiz_json = json.loads(response['message']['content'])
            for item in quiz_json.get("quiz", []):
                all_questions.append(
                    Question(
                        item.get("id"),
                        item.get("type"),
                        item.get("question"),
                        item.get("options", []),
                        item.get("answer", "")   # ✅ use .get with default empty string
                    )
                )
        
        return Quiz(all_questions)
    
    def _build_prompt(self, text, total_q, n_mcq, n_tf, n_written):
        return """
                You are an expert quiz generator.

                Task:
                - Create exactly {n_questions} quiz questions from the provided text.
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
                - MCQ → provide 4 options, correct one must match "answer"
                - No explanation, no extra commentary, ONLY valid JSON.
                Text:
                ---
                {source_text}
                ---
                """