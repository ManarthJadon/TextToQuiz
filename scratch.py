from google import genai
from google.genai import types
from pydantic import BaseModel


class Question(BaseModel):
    question: str
    options: list[str]
    answer_index: int
    explanation: str


class Quiz(BaseModel):
    questions: list[Question]


client = genai.Client()  # reads GEMINI_API_KEY from the environment

text = "The sun is a star at the center of our solar system. Earth orbits it once every 365 days."
difficulty = "easy"
count = 3

prompt = (
    f"Make {count} multiple-choice questions at {difficulty} difficulty "
    f"from the text below. Give 4 options per question.\n\n{text}"
)

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=Quiz,
    ),
)

for i, q in enumerate(response.parsed.questions, start=1):
    print(f"{i}. {q.question}")
    for j, option in enumerate(q.options):
        print(f"   {j}) {option}")
    print(f"   Answer: {q.options[q.answer_index]}")
    print(f"   Why: {q.explanation}\n")