# Text to Quiz

Turn study notes, PDFs, slides, and pasted text into a smart multiple-choice quiz in seconds.

Text to Quiz is a lightweight AI-powered study assistant that extracts text from your files, sends it to Google Gemini, and turns it into a quiz with instant scoring and explanations. It’s built for[...]

## Why use it?

- Upload notes, PDFs, Word docs, slides, or plain text
- Generate quiz questions in different difficulty levels
- Test your knowledge with instant feedback
- Review explanations for every answer
- Stay focused with a simple, no-fuss interface

## How it works

1. Your file or pasted text is converted into plain text
2. The content is sent to Google Gemini using a strict JSON schema
3. A quiz is generated with multiple-choice questions and answers
4. The app shows the quiz, scores your answers, and explains each result

This makes it easy to turn reading material into active recall practice in just a few clicks.

## Features

- Supports `.pdf`, `.docx`, `.pptx`, `.txt`, and `.md` files
- Accepts pasted text directly from the browser
- Choose difficulty: easy, medium, or hard
- Choose between 1 and 20 questions
- Correct answers highlight in green
- Wrong answers highlight in red
- Each question includes a score and explanation

## Tech stack

- Python
- FastAPI
- Google Gemini API (`google-genai`)
- Vanilla HTML, CSS, and JavaScript

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
uvicorn main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```
## Run the tests

```bash
uv pip install -r requirements-dev.txt
```

```bash
pytest
```

The tests use a fake Gemini client, so they need no API key and make no network calls.

## API

| Endpoint | Description |
|---|---|
| `GET /` | Loads the web interface |
| `POST /quiz` | Accepts `{text, count, difficulty}` and returns a quiz |
| `POST /upload` | Accepts a form upload with `file`, `count`, and `difficulty` |

Interactive API docs are available at:

```text
http://127.0.0.1:8000/docs
```

## Project structure

```text
main.py          FastAPI app, file parsing, and Gemini calls
index.html       Frontend page layout
static/style.css Styling and UI
static/app.js    Form logic, quiz rendering, and scoring
```

## ⚠️ Limitations

- Text must be 50 to 200,000 characters, and uploads can be at most 10 MB.
- Scanned PDFs without selectable text are not supported.
- Gemini can be busy at times and return an error. Try again in a moment.

## Roadmap

**Done**

- ~~Support long documents~~ Raised the limit to 200,000 characters
- ~~Tests and Docker support~~
- ~~Read tables in Word and PowerPoint files~~

**Next**

- Launch a live demo
- Refreshed design

**Better learning**

- Show the source sentence from your notes for each answer
- Retake only the questions you missed
- Weak-topic summary after each quiz
- Explain why the wrong options are wrong
- Flashcards
- Exam mode with a timer
- More question types (true/false, fill in the blank)

**Exam preparation**

- Analyze previous year question papers and highlight the most important topics
- Generate a practice question paper from previous year papers

**Platform**

- Cache results to save API quota
- Run the tests automatically on every push (GitHub Actions)
- Export a quiz as PDF
- User accounts and saved quiz history
- Paid plans for higher usage

## Built for learning smarter

Text to Quiz helps turn passive reading into active learning. Whether you’re revising for an exam, preparing for interviews, or just testing your understanding, this app turns your material into a q[...]

**Live demo:** https://texttoquiz.onrender.com