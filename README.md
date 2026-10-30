# Text to Quiz

Turn study notes, PDFs, slides, and pasted text into a smart multiple-choice quiz, a deck of flashcards, or clear study notes in seconds.

Text to Quiz is a lightweight AI-powered study assistant that extracts text from your files, sends it to Google Gemini, and turns it into a quiz with instant scoring and explanations, flashcards you flip to test yourself, or study notes with the key points marked. It’s built for students, self-learners, and anyone who wants a faster way to review material.

**Live demo:** https://texttoquiz.onrender.com

## Why use it?

- Upload notes, PDFs, Word docs, slides, or plain text
- Generate quiz questions in different difficulty levels
- Test your knowledge with instant feedback
- Review explanations for every answer
- Revise with flashcards you flip to check yourself
- Get study notes with the most important points marked
- Stay focused with a simple, no-fuss interface

## How it works

1. Your file or pasted text is converted into plain text
2. The content is sent to Google Gemini using a strict JSON schema
3. Gemini writes multiple-choice questions, flashcards with a front and a back, or structured study notes
4. The app shows the quiz and scores your answers, shows the cards in a grid you can flip, or shows notes you can print, save as PDF, or copy

This makes it easy to turn reading material into active recall practice in just a few clicks.

## Features

- Three modes: **Quiz**, **Flashcards**, or **Notes**
- Supports `.pdf`, `.docx`, `.pptx`, `.txt`, and `.md` files
- Accepts pasted text directly from the browser
- Quiz and flashcards: choose difficulty (easy, medium, or hard) and between 1 and 20 questions or cards
- Quiz: correct answers highlight in green, wrong answers in red, and each question includes an explanation
- Flashcards: key terms become term → definition, ideas become question → short answer; click a card (or press Enter on it) to flip it
- Notes: a short summary, one section per topic with ★ on the points most likely to come up in an exam, and a key terms list
- Notes: choose how detailed they are (short, standard, or detailed)
- Notes: print or save as PDF (only the notes are printed), or copy them as plain text

## Tech stack

- Python
- FastAPI
- Google Gemini API (`google-genai`)
- Vanilla HTML, CSS, and JavaScript
- Docker, hosted on Render
- GitHub Actions for automatic tests

## Quick start

You’ll need Python 3.14 and a free Gemini API key from Google AI Studio.

### 1) Create a virtual environment

```bash
uv venv
```

### 2) Install dependencies

```bash
uv pip install -r requirements.txt
```

### 3) Add your Gemini API key

On PowerShell:

```bash
setx GEMINI_API_KEY "your-key-here"
```

Open a new terminal after setting it.

### 4) Start the app

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

## Run with Docker

```bash
docker build -t text-to-quiz .
```

```bash
docker run --rm -p 8000:8000 -e GEMINI_API_KEY text-to-quiz
```

`-e GEMINI_API_KEY` passes the key from your terminal into the container, so the key is never written in a file.

## Run the tests

```bash
uv pip install --group dev
```

```bash
pytest
```

The tests use a fake Gemini client, so they need no API key and make no network calls. They also run automatically on every push to GitHub.

## API

| Endpoint | Description |
|---|---|
| `GET /` | Loads the web interface |
| `GET /health` | Health check used by the host |
| `POST /quiz` | Accepts `{text, mode, count, difficulty, detail}` and returns a quiz, flashcards, or notes |
| `POST /upload` | Accepts a form upload with `file`, `mode`, `count`, `difficulty`, and `detail` |

| Field | Values | Used by |
|---|---|---|
| `mode` | `quiz` (default), `flashcards`, `notes` | all |
| `count` | 1 to 20 (default 5) | quiz, flashcards |
| `difficulty` | `easy`, `medium` (default), `hard` | quiz, flashcards |
| `detail` | `short`, `standard` (default), `detailed` | notes |

What comes back:

- Quiz: `{"questions": [{"question", "options", "answer_index", "explanation"}]}`
- Flashcards: `{"cards": [{"front", "back"}]}`
- Notes: `{"summary", "sections": [{"heading", "points": [{"text", "important"}]}], "key_terms": [{"term", "meaning"}]}`

Interactive API docs are available at:

```text
http://127.0.0.1:8000/docs
```

## Project structure

```text
app/
  main.py          FastAPI routes, input limits, and per-visitor rate limit
  extract.py       Reads text from PDF, Word, PowerPoint, .txt and .md files
  ai.py            Gemini calls, quiz, flashcard and notes schemas, model fallback, and retries
  static/          Frontend: index.html, style.css, app.js
tests/             Automated tests (run with pytest)
.github/workflows/ Runs the tests on every push
Dockerfile         Builds the container the live site runs in
pyproject.toml     Project info, dependencies, test tools, and test settings
requirements.txt   Exact pinned versions (generated from pyproject.toml)
```

## ⚠️ Limitations

- Text must be 50 to 200,000 characters, and uploads can be at most 10 MB.
- Each visitor can make up to 5 requests per minute and 15 per day, shared by quizzes, flashcards, and notes.
- Scanned PDFs without selectable text are not supported.
- Gemini can be busy at times and return an error. Try again in a moment.

## Roadmap

**Done**

- ~~Support long documents~~ Raised the limit to 200,000 characters
- ~~Tests and Docker support~~
- ~~Read tables in Word and PowerPoint files~~
- ~~Launch a live demo~~
- ~~Run the tests automatically on every push (GitHub Actions)~~
- ~~Flashcards~~
- ~~Study notes with key points and important topics~~

**Next**

- Images and scanned or handwritten PDFs
- Maths equations shown properly

**Better learning**

- Show the source sentence from your notes for each answer
- Retake only the questions you missed
- Weak-topic summary after each quiz
- Explain why the wrong options are wrong
- Exam mode with a timer
- More question types (true/false, fill in the blank)

**Exam preparation**

- Analyze previous year question papers and highlight the most important topics
- Generate a practice question paper from previous year papers

**Platform**

- Cache results to save API quota
- Export a quiz as PDF
- User accounts and saved quiz history
- Paid plans for higher usage

## Built for learning smarter

Text to Quiz helps turn passive reading into active learning. Whether you’re revising for an exam, preparing for interviews, or just testing your understanding, this app turns your material into a quick, interactive quiz, a deck of flashcards, or clear study notes.
