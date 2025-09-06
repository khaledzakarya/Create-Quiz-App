# Create Quiz API

An AI-powered API to **generate quizzes from PDF documents**.  
It supports **multi-language prompts (English & Arabic)**, different question types (**MCQ, True/False, Written**),  
and allows flexible quiz generation either from **all pages** or **specific focus/remaining pages**.

---

##  Features
-  Extracts text from **PDF files**.
-  Generates structured quiz questions using **LLM (Ollama, Gemma)**.
- Supports **multi-language prompts** (English & Arabic).
- Allows **focus/remaining pages** selection or full-document quiz creation.
- Customizable distribution of question types:
  - Multiple Choice Questions (MCQ)
  - True/False Questions
  - Written Questions
- Modular design:
  - `PDFReader` → extract PDF text
  - `QuestionGenerator` → generate raw questions
  - `QuestionSelector` → ensure diversity & balance
  - `TemplateParser` → load prompts in multiple languages

---

## 📂 Project Structure
```
src
├── controller # Logic for reading PDFs, generating & selecting questions
│ ├── init.py
│ ├── PDFReader.py # Extracts and processes text from PDF files
│ ├── QuestionGenerator.py # Generates quiz questions using LLM + templates
│ └── QuestionSelector.py # Selects diverse & balanced set of questions
│
├── data
│ └── sample.pdf # Example input PDF file
│
├── helpers
│ ├── init.py
│ └── config.py # App settings and configuration
│
├── models
│ ├── enums
│ │ ├── init.py
│ │ └── QuestionTypeEnum.py # Enum for question types (MCQ, True/False, Written)
│ ├── init.py
│ └── quiz.py # Data models for Quiz and Question objects
│
├── notebooks
│ └── prefinal_Create_Quizes.ipynb # Jupyter notebook for experimentation
│
├── routes
│ ├── schema
│ │ ├── init.py
│ │ └── QuizRequest.py # Request schema (Pydantic) for API validation
│ ├── init.py
│ └── generate_quiz.py # FastAPI route to generate quiz from PDF
│
├── stores
│ ├── init.py
│ └── llm
│ ├── templates
│ │ ├── init.py
│ │ ├── template_parser.py # Handles loading prompts in different languages
│ │ └── locales
│ │ ├── init.py
│ │ ├── ar
│ │ │ ├── init.py
│ │ │ └── prompt.py # Arabic quiz generation prompt
│ │ └── en
│ │ ├── init.py
│ │ └── prompt.py # English quiz generation prompt
│ ├── init.py
│ └── quiz_service.py # Main service: integrates reader, generator, and selector
│
└── main.py # FastAPI app entry point (runs the server)
```

---

## Installation & Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/<your-org>/<your-repo>.git
   cd <your-repo>
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux / Mac
   venv\Scripts\activate      # Windows
   ```

3. Setup the environment variables
    ```bash
    $ cp .env.example .env
    ```  

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

---

## API Endpoints

### Generate Quiz
```http
POST /ai/generate_quiz/
```

#### Request Body
```json
{
  "pdf_path": "uploads/sample.pdf",
  "level": "medium",
  "language": "en",
  "n_questions": 15,
  "f_mcq_ratio": 0.6,
  "f_tf_ratio": 0.2,
  "f_written_ratio": 0.2
}
```

#### Example with Focus & Remaining Pages
```json
{
  "pdf_path": "uploads/sample.pdf",
  "level": "hard",
  "language": "ar",
  "focus_pages": [1, 2],
  "remain_pages": [3, 4],
  "n_focus": 10,
  "n_remain": 5,
  "f_mcq_ratio": 0.6,
  "f_tf_ratio": 0.2,
  "f_written_ratio": 0.2,
  "r_mcq_ratio": 0.8,
  "r_tf_ratio": 0.1,
  "r_written_ratio": 0.1
}
```

#### Response
```json
[
  {
    "type": "MCQ",
    "question": "What is ...?",
    "options": ["A", "B", "C", "D"],
    "answer": "B"
  },
  {
    "type": "TrueFalse",
    "question": "X is correct?",
    "options": [],
    "answer": "True"
  },
  {
    "type": "Written",
    "question": "Explain Y?",
    "options": [],
    "answer": "Y is ..."
  }
]
```

