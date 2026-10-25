"""The web server: pages, endpoints, input checks and rate limits."""
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app import ai
from app.extract import prepare_upload

MAX_CHARS = 200_000
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
RATE_LIMIT = "5/minute;15/day"  # per IP, shared by /quiz and /upload
STATIC_DIR = Path(__file__).parent / "static"  # works no matter which folder you start from
PROXIES_AFTER_VISITOR = 2  # Render's proxies add 2 IPs after the visitor's own
MAKERS = {"quiz": ai.make_quiz, "flashcards": ai.make_flashcards}  # modes that use count and difficulty


def client_ip(request: Request) -> str:
    # Visitors can fake the start of X-Forwarded-For, but not what Render adds at the end
    parts = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
    if len(parts) > PROXIES_AFTER_VISITOR:
        return parts[-PROXIES_AFTER_VISITOR - 1]
    return get_remote_address(request)  # not behind Render (local runs): use the real connection


# ponytail: in-memory counters work for one server instance; use Redis storage if we ever run several
limiter = Limiter(key_func=client_ip)
app = FastAPI()
app.state.limiter = limiter
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class QuizRequest(BaseModel):
    text: str
    count: int = 5
    difficulty: str = "medium"
    mode: str = "quiz"
    detail: str = "standard"


@app.exception_handler(RateLimitExceeded)
def rate_limited(request: Request, exc: RateLimitExceeded):
    if "day" in str(exc.limit.limit):  # e.g. "15 per 1 day"
        message = "You have used all of today's requests, please come back tomorrow"
    else:
        message = "Too many requests, please wait a minute and try again"
    return JSONResponse({"detail": message}, status_code=429)


def checked_make(source, count: int, difficulty: str, mode: str, detail: str):
    # source is text, or a list of photos / a scanned PDF (only text has a length to check)
    if isinstance(source, str) and not 50 <= len(source) <= MAX_CHARS:
        raise HTTPException(400, f"Text must be 50 to {MAX_CHARS:,} characters")
    if mode == "notes":  # notes have a detail level instead of a count and difficulty
        if detail not in ai.DETAIL:
            raise HTTPException(400, "Detail must be short, standard or detailed")
        return ai.make_notes(source, detail)
    if mode not in MAKERS:
        raise HTTPException(400, "Mode must be quiz, flashcards or notes")
    if not 1 <= count <= 20:
        raise HTTPException(400, "Count must be 1 to 20")
    if difficulty not in ("easy", "medium", "hard"):
        raise HTTPException(400, "Difficulty must be easy, medium or hard")
    return MAKERS[mode](source, count, difficulty)


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/quiz")
@limiter.shared_limit(RATE_LIMIT, scope="quiz")
def create_quiz(request: Request, req: QuizRequest):
    return checked_make(req.text, req.count, req.difficulty, req.mode, req.detail)


@app.post("/upload")
@limiter.shared_limit(RATE_LIMIT, scope="quiz")
def upload(
    request: Request,
    file: list[UploadFile] = File(...),  # one document, or several photos under the same field name
    count: int = Form(5),
    difficulty: str = Form("medium"),
    mode: str = Form("quiz"),
    detail: str = Form("standard"),
):
    files, total = [], 0
    for f in file:
        data = f.file.read(MAX_UPLOAD_BYTES + 1 - total)  # never read more than the limit allows
        total += len(data)
        if total > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "File is too large (max 10 MB)")
        files.append((f.filename, data))
    try:
        source = prepare_upload(files)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(400, "Could not read this file")
    return checked_make(source, count, difficulty, mode, detail)