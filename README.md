# Text to Quiz

Turn study notes, PDFs, slides, and pasted text into a smart multiple-choice quiz in seconds.

Text to Quiz is a lightweight AI-powered study assistant that extracts text from your files, sends it to Google Gemini, and turns it into a quiz with instant scoring and explanations. It’s built for students, self-learners, and anyone who wants a faster way to review material.

![Text to Quiz screenshot](docs/screenshot.png)

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

## Current limitations

- Input text must be between 50 and 20,000 characters
- PDFs with scanned or non-selectable text may not work correctly

## Roadmap

- Support long documents by splitting content into chunks
- Launch a live demo
- Add tests and Docker support
- Let users retake only the questions they missed

## Built for learning smarter

Text to Quiz helps turn passive reading into active learning. Whether you’re revising for an exam, preparing for interviews, or just testing your understanding, this app turns your material into a quick, interactive quiz experience.
