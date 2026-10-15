"""Everything that talks to Gemini: the models, the answer shapes and the prompts."""
from fastapi import HTTPException
from google import genai
from google.genai import types
from pydantic import BaseModel

# Tried in order: each model has its own free quota, so a busy or used-up model falls through to the next
MODELS = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"]

client = genai.Client(  # reads GEMINI_API_KEY from the environment
    http_options=types.HttpOptions(
        timeout=60_000,  # milliseconds, per try
        retry_options=types.HttpRetryOptions(
            attempts=2,  # total tries per model, including the first
            initial_delay=1.0,
            http_status_codes=[500, 503, 504],
        ),
    )
)


class Question(BaseModel):
    question: str
    options: list[str]
    answer_index: int
    explanation: str


class Quiz(BaseModel):
    questions: list[Question]


def generate(prompt: str, schema, is_valid):
    """Asks each model in turn for an answer shaped like `schema`; returns the first one `is_valid` accepts."""
    error = None
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
        except Exception as e:
            print(f"GEMINI ERROR ({model}):", e)
            error = e
            continue
        if response.parsed and is_valid(response.parsed):
            return response.parsed
        print(f"GEMINI BAD ANSWER ({model})")

    code = getattr(error, "code", None)  # Gemini errors carry the HTTP status
    if code == 429:
        raise HTTPException(429, "The free daily limit is used up, please try again tomorrow")
    if code in (503, 504):
        raise HTTPException(503, "Gemini is busy right now, please try again in a minute")
    raise HTTPException(502, "Gemini request failed, try again")


def quiz_is_valid(quiz: Quiz) -> bool:
    # Only accept quizzes the page can show: 4 options and a valid answer
    return bool(quiz.questions) and all(
        len(q.options) == 4 and 0 <= q.answer_index < 4 for q in quiz.questions
    )


def make_quiz(text: str, count: int, difficulty: str) -> Quiz:
    prompt = (
        f"Make {count} multiple-choice questions at {difficulty} difficulty "
        f"from the text below. Give 4 options per question, with exactly one correct. "
        f"Ask about the subject matter and ideas in the text. Ignore general "
        f"instructions, headers, page numbers, marks, time limits and formatting notes. "
        f"Spread the questions across the whole text.\n\n{text}"
    )
    return generate(prompt, Quiz, quiz_is_valid)
