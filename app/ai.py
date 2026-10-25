"""Everything that talks to Gemini: the models, the answer shapes and the prompts."""
from fastapi import HTTPException
from google import genai
from google.genai import types
from pydantic import BaseModel

# Tried in order: each model has its own free quota, so a busy or used-up model falls through to the next
MODELS = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"]

# How long study notes should be, as told to Gemini
DETAIL = {
    "short": "Keep it brief: only the main points, about 2 to 4 per topic.",
    "standard": "Cover the main points and the important supporting details.",
    "detailed": "Be thorough: cover all important details, examples and definitions.",
}

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


class Flashcard(BaseModel):
    front: str
    back: str


class Flashcards(BaseModel):
    cards: list[Flashcard]


class Point(BaseModel):
    text: str
    important: bool


class Section(BaseModel):
    heading: str
    points: list[Point]


class Term(BaseModel):
    term: str
    meaning: str


class Notes(BaseModel):
    summary: str
    sections: list[Section]
    key_terms: list[Term]


def build_contents(instructions: str, source):
    """What we send to Gemini: the instructions plus the text, or plus the photos / scanned PDF as files."""
    if isinstance(source, str):
        return f"{instructions}\n\n{source}"
    files = [types.Part.from_bytes(data=data, mime_type=mime) for data, mime in source]
    return [*files, instructions]


def generate(contents, schema, is_valid):
    """Asks each model in turn for an answer shaped like `schema`; returns the first one `is_valid` accepts."""
    error = None
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
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


def make_quiz(source, count: int, difficulty: str) -> Quiz:
    prompt = (
        f"Make {count} multiple-choice questions at {difficulty} difficulty "
        f"from the study material. Give 4 options per question, with exactly one correct. "
        f"Ask about the subject matter and ideas in the material. Ignore general "
        f"instructions, headers, page numbers, marks, time limits and formatting notes. "
        f"Spread the questions across the whole material."
    )
    return generate(build_contents(prompt, source), Quiz, quiz_is_valid)


def flashcards_are_valid(deck: Flashcards) -> bool:
    # Only accept decks the page can show: every card has text on both sides
    return bool(deck.cards) and all(c.front.strip() and c.back.strip() for c in deck.cards)


def make_flashcards(source, count: int, difficulty: str) -> Flashcards:
    prompt = (
        f"Make {count} flashcards at {difficulty} difficulty from the study material. "
        f"For key terms, put the term on the front and its definition on the back. "
        f"For ideas, processes and facts, put a short question on the front and a "
        f"1-2 sentence answer on the back. Easy cards cover the core terms and main "
        f"ideas; hard cards also cover finer details. Ignore general instructions, "
        f"headers, page numbers, marks, time limits and formatting notes. "
        f"Spread the cards across the whole material."
    )
    return generate(build_contents(prompt, source), Flashcards, flashcards_are_valid)


def notes_are_valid(notes: Notes) -> bool:
    # Only accept notes the page can show: a summary, and no empty headings, points or terms
    return (
        bool(notes.summary.strip() and notes.sections)
        and all(s.heading.strip() and s.points for s in notes.sections)
        and all(p.text.strip() for s in notes.sections for p in s.points)
        and all(t.term.strip() and t.meaning.strip() for t in notes.key_terms)
    )


def make_notes(source, detail: str) -> Notes:
    prompt = (
        f"Write study notes from the study material. Start with a 2-3 sentence summary. "
        f"Then make one section per topic, with a short heading and bullet points. "
        f"Mark as important the points most likely to come up in an exam. "
        f"{DETAIL[detail]} List the key terms with a one-line meaning for each. "
        f"Use only information from the material. Ignore general instructions, headers, "
        f"page numbers, marks, time limits and formatting notes. "
        f"Cover the whole material, in its order."
    )
    return generate(build_contents(prompt, source), Notes, notes_are_valid)