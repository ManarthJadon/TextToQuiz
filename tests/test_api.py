import io
import os
import time
from types import SimpleNamespace

os.environ.setdefault("GEMINI_API_KEY", "test-key")  # app/ai.py creates the Gemini client on import

import limits.storage.memory
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app import ai, main

api = TestClient(main.app)
TEXT = "The sun is a star at the center of our solar system. " * 2
FAKE_QUIZ = ai.Quiz(
    questions=[
        ai.Question(
            question="What is the sun?",
            options=["A star", "A planet", "A moon", "A comet"],
            answer_index=0,
            explanation="The sun is a star.",
        )
    ]
)
FAKE_DECK = ai.Flashcards(
    cards=[ai.Flashcard(front="Sun", back="The star at the center of our solar system.")]
)
FAKE_NOTES = ai.Notes(
    summary="The sun is the star at the center of our solar system.",
    sections=[ai.Section(heading="The sun", points=[ai.Point(text="The sun is a star", important=True)])],
    key_terms=[ai.Term(term="Star", meaning="A huge ball of hot gas that gives off light")],
)


def upload(name, data, **form):
    fields = {"count": "3", "difficulty": "easy", **form}
    return api.post("/upload", files={"file": (name, data)}, data=fields)


def upload_many(files, **form):
    # Several files under the same field name "file", like the page sends photos
    fields = {"count": "3", "difficulty": "easy", **form}
    return api.post("/upload", files=[("file", f) for f in files], data=fields)


def fake_client(generate_content):
    return SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))


def fake_answer(**kw):
    # Answer in whatever shape the app asked for: a quiz, a flashcard deck or notes
    answers = {ai.Quiz: FAKE_QUIZ, ai.Flashcards: FAKE_DECK, ai.Notes: FAKE_NOTES}
    return SimpleNamespace(parsed=answers[kw["config"].response_schema])


@pytest.fixture
def fake_gemini(monkeypatch):
    monkeypatch.setattr(ai, "client", fake_client(fake_answer))


@pytest.fixture
def sent(monkeypatch):
    # A fake Gemini that also remembers what the app sent it
    contents = []

    def remember(**kw):
        contents.append(kw["contents"])
        return fake_answer(**kw)

    monkeypatch.setattr(ai, "client", fake_client(remember))
    return contents


@pytest.fixture
def broken_gemini(monkeypatch):
    def boom(**kw):
        raise RuntimeError("Gemini is down")

    monkeypatch.setattr(ai, "client", fake_client(boom))


@pytest.fixture(autouse=True)
def reset_limiter():
    main.limiter.reset()


# --- pages ---

def test_home_page():
    assert api.get("/").status_code == 200


def test_health():
    assert api.get("/health").json() == {"status": "ok"}


# --- /quiz ---

def test_quiz_ok(fake_gemini):
    r = api.post("/quiz", json={"text": TEXT, "count": 1, "difficulty": "easy"})
    assert r.status_code == 200
    assert r.json()["questions"][0]["answer_index"] == 0


def test_quiz_text_too_short():
    assert api.post("/quiz", json={"text": "short"}).status_code == 400


def test_quiz_text_too_long():
    r = api.post("/quiz", json={"text": "a" * (main.MAX_CHARS + 1)})
    assert r.status_code == 400


@pytest.mark.parametrize("count", [0, 21])
def test_quiz_bad_count(count):
    assert api.post("/quiz", json={"text": TEXT, "count": count}).status_code == 400


def test_quiz_bad_difficulty():
    assert api.post("/quiz", json={"text": TEXT, "difficulty": "insane"}).status_code == 400


def test_quiz_bad_mode():
    r = api.post("/quiz", json={"text": TEXT, "mode": "poem"})
    assert r.status_code == 400
    assert r.json()["detail"] == "Mode must be quiz, flashcards or notes"


# --- flashcards ---

def test_flashcards_ok(fake_gemini):
    r = api.post("/quiz", json={"text": TEXT, "count": 1, "mode": "flashcards"})
    assert r.status_code == 200
    assert r.json()["cards"][0]["front"] == "Sun"


def test_upload_flashcards_ok(fake_gemini):
    r = upload("notes.txt", TEXT.encode(), mode="flashcards")
    assert r.status_code == 200
    assert r.json()["cards"][0]["back"] == "The star at the center of our solar system."


def test_flashcards_reject_blank_card(monkeypatch):
    blank = ai.Flashcards(cards=[ai.Flashcard(front="Sun", back="   ")])
    monkeypatch.setattr(ai, "client", fake_client(lambda **kw: SimpleNamespace(parsed=blank)))
    r = api.post("/quiz", json={"text": TEXT, "mode": "flashcards"})
    assert r.status_code == 502


# --- study notes ---

def test_notes_ok(fake_gemini):
    r = api.post("/quiz", json={"text": TEXT, "mode": "notes", "detail": "short"})
    assert r.status_code == 200
    notes = r.json()
    assert notes["sections"][0]["points"][0] == {"text": "The sun is a star", "important": True}
    assert notes["key_terms"][0]["term"] == "Star"


def test_upload_notes_ok(fake_gemini):
    r = upload("notes.txt", TEXT.encode(), mode="notes", detail="detailed")
    assert r.status_code == 200
    assert r.json()["summary"] == FAKE_NOTES.summary


def test_notes_detail_reaches_prompt(monkeypatch):
    prompts = []

    def remember(**kw):
        prompts.append(kw["contents"])
        return SimpleNamespace(parsed=FAKE_NOTES)

    monkeypatch.setattr(ai, "client", fake_client(remember))
    api.post("/quiz", json={"text": TEXT, "mode": "notes", "detail": "detailed"})
    assert ai.DETAIL["detailed"] in prompts[0]


def test_notes_ignore_count_and_difficulty(fake_gemini):
    # The page hides these fields in notes mode, so leftover values must not cause errors
    r = api.post("/quiz", json={"text": TEXT, "mode": "notes", "count": 99, "difficulty": "insane"})
    assert r.status_code == 200


def test_notes_bad_detail():
    r = api.post("/quiz", json={"text": TEXT, "mode": "notes", "detail": "huge"})
    assert r.status_code == 400
    assert r.json()["detail"] == "Detail must be short, standard or detailed"


def test_notes_reject_empty_sections(monkeypatch):
    empty = FAKE_NOTES.model_copy(update={"sections": []})
    monkeypatch.setattr(ai, "client", fake_client(lambda **kw: SimpleNamespace(parsed=empty)))
    r = api.post("/quiz", json={"text": TEXT, "mode": "notes"})
    assert r.status_code == 502


# --- Gemini problems ---

def test_quiz_gemini_failure(broken_gemini):
    assert api.post("/quiz", json={"text": TEXT}).status_code == 502


def test_quiz_falls_back_to_next_model(monkeypatch):
    calls = []

    def flaky(**kw):
        calls.append(kw["model"])
        if len(calls) == 1:
            raise RuntimeError("first model is busy")
        return SimpleNamespace(parsed=FAKE_QUIZ)

    monkeypatch.setattr(ai, "client", fake_client(flaky))
    r = api.post("/quiz", json={"text": TEXT, "count": 1, "difficulty": "easy"})
    assert r.status_code == 200
    assert calls == ai.MODELS[:2]


def test_quiz_rejects_bad_answer_index(monkeypatch):
    bad = ai.Quiz(questions=[FAKE_QUIZ.questions[0].model_copy(update={"answer_index": 7})])
    monkeypatch.setattr(ai, "client", fake_client(lambda **kw: SimpleNamespace(parsed=bad)))
    r = api.post("/quiz", json={"text": TEXT, "count": 1, "difficulty": "easy"})
    assert r.status_code == 502


# --- /upload ---

def test_upload_ok(fake_gemini):
    r = upload("notes.txt", TEXT.encode())
    assert r.status_code == 200
    assert r.json()["questions"][0]["question"] == "What is the sun?"


def test_upload_unsupported_type():
    assert upload("a.exe", b"x").status_code == 400


def test_upload_unreadable_file():
    assert upload("a.pdf", b"not really a pdf").status_code == 400


def test_upload_too_large():
    assert upload("big.txt", b"a" * (main.MAX_UPLOAD_BYTES + 1)).status_code == 413


# --- photos and scanned PDFs ---

def test_upload_photos_sent_as_images(sent):
    r = upload_many([("page1.jpg", b"img1"), ("page2.png", b"img2")])
    assert r.status_code == 200
    *photos, instructions = sent[0]
    assert [p.inline_data.mime_type for p in photos] == ["image/jpeg", "image/png"]
    assert [p.inline_data.data for p in photos] == [b"img1", b"img2"]
    assert "multiple-choice" in instructions


def test_upload_scanned_pdf_sent_as_pdf(sent):
    buf = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)  # a page with no text, like a scan
    writer.write(buf)
    r = upload("scan.pdf", buf.getvalue(), mode="notes")
    assert r.status_code == 200
    assert sent[0][0].inline_data.mime_type == "application/pdf"


def test_upload_text_still_sent_as_text(sent):
    upload("notes.txt", TEXT.encode())
    assert isinstance(sent[0], str) and TEXT in sent[0]


def test_upload_photo_mixed_with_document():
    r = upload_many([("page.jpg", b"x"), ("notes.txt", TEXT.encode())])
    assert r.status_code == 400
    assert "one document" in r.json()["detail"]


def test_upload_photos_too_large_together():
    half = b"a" * (main.MAX_UPLOAD_BYTES // 2 + 1)  # each photo is fine, both together are not
    assert upload_many([("a.jpg", half), ("b.jpg", half)]).status_code == 413


# --- rate limits and visitor IP ---

def test_rate_limit(fake_gemini):
    n = 5  # the per-minute limit
    responses = [api.post("/quiz", json={"text": TEXT}) for _ in range(n + 1)]
    assert [r.status_code for r in responses] == [200] * n + [429]
    assert "wait a minute" in responses[-1].json()["detail"]


def test_rate_limit_shared_by_quiz_and_flashcards(fake_gemini):
    for _ in range(5):  # use up the per-minute limit with quizzes
        assert api.post("/quiz", json={"text": TEXT}).status_code == 200
    r = api.post("/quiz", json={"text": TEXT, "mode": "flashcards"})
    assert r.status_code == 429


def test_daily_limit(fake_gemini, monkeypatch):
    clock = [time.time()]
    # The rate limiter reads this clock, so the test can jump ahead a minute without waiting
    monkeypatch.setattr(limits.storage.memory, "time", SimpleNamespace(time=lambda: clock[0]))
    codes = []
    for _ in range(16):
        clock[0] += 61  # a new minute each time, so only the daily limit can block
        codes.append(api.post("/quiz", json={"text": TEXT}).status_code)
    assert codes == [200] * 15 + [429]
    assert "tomorrow" in api.post("/quiz", json={"text": TEXT}).json()["detail"]


def test_client_ip_ignores_faked_header_entries():
    def request(forwarded):
        headers = {"x-forwarded-for": forwarded} if forwarded else {}
        return SimpleNamespace(headers=headers, client=SimpleNamespace(host="127.0.0.1"))

    # Render adds: visitor, Cloudflare, internal. Anything before the visitor is faked.
    assert main.client_ip(request("1.2.3.4, 162.158.1.1, 10.0.0.1")) == "1.2.3.4"
    assert main.client_ip(request("9.9.9.9,1.2.3.4, 162.158.1.1, 10.0.0.1")) == "1.2.3.4"
    assert main.client_ip(request(None)) == "127.0.0.1"  # no proxy, e.g. running locally