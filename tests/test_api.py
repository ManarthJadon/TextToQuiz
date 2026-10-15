import os
import time
from types import SimpleNamespace

os.environ.setdefault("GEMINI_API_KEY", "test-key")  # app/ai.py creates the Gemini client on import

import limits.storage.memory
import pytest
from fastapi.testclient import TestClient

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


def upload(name, data, **form):
    fields = {"count": "3", "difficulty": "easy", **form}
    return api.post("/upload", files={"file": (name, data)}, data=fields)


def fake_client(generate_content):
    return SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))


@pytest.fixture
def fake_gemini(monkeypatch):
    monkeypatch.setattr(ai, "client", fake_client(lambda **kw: SimpleNamespace(parsed=FAKE_QUIZ)))


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


# --- rate limits and visitor IP ---

def test_rate_limit(fake_gemini):
    n = 5  # the per-minute limit
    responses = [api.post("/quiz", json={"text": TEXT}) for _ in range(n + 1)]
    assert [r.status_code for r in responses] == [200] * n + [429]
    assert "wait a minute" in responses[-1].json()["detail"]


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
