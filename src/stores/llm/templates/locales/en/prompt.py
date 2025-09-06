from string import Template
quiz_prompt = Template(
    """
    You are an expert quiz generator.
    
    Task:
    - Create exactly ${total_q} quiz questions from the provided text.
    - Difficulty Level: ${level}
    - Distribution:
      • ${n_mcq} Multiple Choice Questions (4 options)
      • ${n_tf} True/False Questions
      • ${n_written} Written Questions

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
    - Difficulty Level (${level}) must be reflected in how complex the questions and answers are.
    - No explanation, no extra commentary, ONLY valid JSON.
    - Quiz must be in English
    Text:
    ---
    ${text}
    ---
    """
)