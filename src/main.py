from fastapi import FastAPI
from routes import generate_quiz

app = FastAPI()
app.include_router(generate_quiz.generate_router)
