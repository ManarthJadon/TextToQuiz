import io

from docx import Document
from fastapi import FastAPI, HTTPException
from google import genai
from google.genai import types
from pptx import Presentation
from pydantic import BaseModel
from pypdf import PdfReader

app = FastAPI()
client = genai.Client()  # reads GEMINI_API_KEY from the environment


class Question(BaseModel):
    question: str
    options: list[str]
    answer_index: int
    explanation: str


class Quiz(BaseModel):
    questions: list[Question]


class QuizRequest(BaseModel):
    text: str
    count: int = 5
    difficulty: str = "medium"


def extract_text(filename: str, data: bytes) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if ext == "docx":
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    if ext == "pptx":
        prs = Presentation(io.BytesIO(data))
        return "\n".join(
            shape.text_frame.text
            for slide in prs.slides
            for shape in slide.shapes
            if shape.has_text_frame
        )
    if ext in ("txt", "md"):
        return data.decode("utf-8", errors="ignore")
    raise ValueError(f"Unsupported file type: .{ext}")


@app.get("/")
def home():
    return {"status": "ok"}


@app.post("/quiz")
def create_quiz(req: QuizRequest):
    if not 50 <= len(req.text) <= 20000:
        raise HTTPException(400, "Text must be 50 to 20,000 characters")
    if not 1 <= req.count <= 20:
        raise HTTPException(400, "Count must be 1 to 20")
    if req.difficulty not in ("easy", "medium", "hard"):
        raise HTTPException(400, "Difficulty must be easy, medium or hard")

    prompt = (
        f"Make {req.count} multiple-choice questions at {req.difficulty} difficulty "
        f"from the text below. Give 4 options per question.\n\n{req.text}"
    )
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Quiz,
            ),
        )
    except Exception as e:
        print("GEMINI ERROR:", e)
        raise HTTPException(502, "Gemini request failed, try again")
    return response.parsed