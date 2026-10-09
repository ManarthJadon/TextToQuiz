# active-memory handoff: Text-to-Quiz (AI quiz generator)

**Handoff #1** · 2026-10-09 · Lineage: #1 (2026-10-09): setup and Step 1 done, scope corrected to file upload plus difficulty, Step 2 next

## 0. Instructions for Claude (read first)

You are continuing work from a previous chat. That chat is gone; this file is the complete context and the source of truth.

1. Read this whole file before replying.
2. Follow sections 3 (Style), 4 (Hard rules) and 5 (Corrections) in every reply, for the rest of this chat. They override your defaults.
3. Use the values in section 8 exactly. Never round, re-estimate, or "correct" them.
4. Do not suggest anything listed in section 7 (Changed / rejected) again unless the user brings it up.
5. Code word: None active. If the user types /amcodeword, start every reply with the phrase they choose (default "Yes Boss!").
6. Your first reply: at most 5 lines covering the goal, the current state, and the next step (section 11). Mention any files from section 13 that were not attached. Ask the questions in section 12 if there are any. End with "Ready to continue with <next step>?" Then wait for the user's go.

## 1. Mission
- **Goal:** Build an AI tool where the user uploads PDF, Word, slides or notes, chooses a difficulty and a number of questions, and gets a multiple-choice quiz with scoring and explanations.
- **Done looks like:** Working web app (FastAPI backend + HTML page), pushed to GitHub with a README, as portfolio project 1 of 5.
- **Why it matters / context:** The user wants an AI job or internship in 4-5 months. Roadmap order: 1 Text-to-Quiz, 2 Voice Translator & Language Tutor, 3 Private Document Assistant (RAG, Ollama, ChromaDB), 4 Personal Finance Assistant, 5 Fraud Detection System.

## 2. About the user (as relevant to this work)
- Learning full-stack (JS, HTML, CSS) in a course ending in 2-3 months, with a 6-month internship after. Learning Python over the next 4 months. Beginner in Python and git.
- Windows 11, PyCharm, PowerShell terminal, Python 3.14.7, uv 0.12.20. Ollama not installed.
- GitHub username: ManarthJadon.

## 3. Style & communication
- **Language:** English.
- **Tone:** Direct, friendly, beginner-level explanations.
- **Reply length:** Short; one step at a time.
- **Formatting:** Each terminal command in its own `bash`-tagged code block (one command per block, no `$` prompt), plain numbered steps, bold step names.
- **Working style:** Step by step. Every step ends with a check the user can run. The user writes the code; Claude guides and reviews. Claude gave the exact `scratch.py` code once when asked directly. Give code only if the user asks.
- **Avoid:** Writing the whole project for the user. Long explanations. Asking the user to paste terminal history. Dumping everything at once.

## 4. Hard rules (word for word)
1. "i want to build this project myself from code to working everything" (the user writes the code).
2. "no i want to build it step my step" (one step at a time).
3. Never put the API key in chat, screenshots or files. Use `GEMINI_API_KEY` as an environment variable and later `.env`, which is in `.gitignore`.
4. Commands go in the terminal; file contents go in the editor, never pasted into the terminal.
5. No pull requests for now; the user pushes straight to `main`.

## 5. Corrections log
| # | Claude did | The user wanted |
|---|---|---|
| 1 | Built the whole project in a scratch folder | "i want to build this project myself from code to working everything" |
| 2 | Treated file upload and the difficulty dropdown as optional extras | "we are build an Ai tool in which we can upload our pdf word docks slides and notes select the difficulty of the quiz and number of questions and it will generate a quiz for us" |
| 3 | Told the user to create `quiz_test.py` | Not needed; Step 2 is done inside `scratch.py` (the user was confused by the extra file) |
| 4 | Suggested `uv add` / `gemini-2.5-flash` | `uv pip install` was needed (no `pyproject.toml`); `gemini-2.5-flash` returns 404, use `gemini-3.8-flash` |

## 6. Decisions
| Decision | Why |
|---|---|
| Project folder `C:\documents\Documents\projects\Ai projects\Text to Quiz` | User's choice |
| Repo https://github.com/ManarthJadon/TextToQuiz.git, push straight to `main` | User's choice; solo project |
| Model `gemini-3.8-flash` | `gemini-2.5-flash` returned 404 for new users; Google's error message named this model |
| One API key per project, named `text-to-quiz` | Easy to track and delete |
| Convert every file type to plain text first, then use one quiz function | Gemini reads PDF but not Word or PowerPoint |
| Do Step 2 in `scratch.py`, delete `scratch.py` later or move its code into `main.py` | Fewer files |

## 7. Changed / rejected
- Claude's finished build in a temporary scratch folder → the user builds it from scratch step by step.
- Difficulty dropdown and PDF upload as "extras" → core features (steps 3 to 6).
- `quiz_test.py` → rejected; use `scratch.py`.
- `gemini-2.5-flash` → `gemini-3.8-flash`.
- First API key (exposed in a screenshot) → deleted; new key created and set.
- ❌ Create PR button / branches → not for now.

## 8. Data & facts (exact)
- Folder: `C:\documents\Documents\projects\Ai projects\Text to Quiz`
- Repo: `https://github.com/ManarthJadon/TextToQuiz.git` (branch `main`)
- Env var: `GEMINI_API_KEY` (set per terminal with `$env:GEMINI_API_KEY = "..."`; lost when a terminal is closed)
- Key page: https://aistudio.google.com/apikey
- Python 3.14.7; uv 0.12.20; installed with `uv pip install fastapi uvicorn google-genai`, saved with `uv pip freeze > requirements.txt`
- Validation rules from the original spec: text must be 50 to 20,000 characters; question count 1 to 20; bad input returns 400; Gemini failure returns 502
- Libraries planned later: `pypdf`, `python-docx`, `python-pptx`, `python-multipart`

## 9. People, terms & names
- **People:** The user (mr.stargazer23@gmail.com). Claude guides.
- **Terms & nicknames:** AFC warning ("Direct use of automatic function calling") is harmless and can be ignored. `response.parsed` holds the structured result.
- **Names in use:** `scratch.py`, `main.py`, `index.html`, `requirements.txt`, `.gitignore`, `Question`, `Quiz`, `answer_index`, `GEMINI_API_KEY`.

## 10. Work state
| Item | Status | Version / location | Notes |
|---|---|---|---|
| Step 0 setup (venv, packages, git init, `.gitignore`, key) | Done | project folder | |
| `scratch.py` (Step 1) | Done, works | project folder | Calls `gemini-3.8-flash`, prints reply |
| Step 1 commit and push | Unconfirmed | | Commands given: `git add scratch.py`, `git commit -m "step 1: gemini call works"`, `git push` |
| `main.py` | PyCharm sample, unused | project folder | Replaced in Step 3 |
| Step 2 structured JSON | Not started | `scratch.py` | |
| Steps 3 to 8 | Not started | | |

Plan:
- Step 2: `Question` (question, options: list[str], answer_index: int, explanation) and `Quiz` (questions: list[Question]); `config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=Quiz)`; add difficulty to the prompt; print `response.parsed.questions` in a loop.
- Step 3: FastAPI `POST /quiz` with `text`, `count`, `difficulty`.
- Step 4: `extract_text(filename, data)` for pdf, docx, pptx, txt and md.
- Step 5: upload endpoint (`UploadFile`, `python-multipart`).
- Step 6: page with file picker, textarea, difficulty dropdown, count.
- Step 7: check answers with score, explanations, red/green.
- Step 8: README with screenshot, push, then project 2.

## 11. Next steps
1. **Next action:** The user edits `scratch.py` for Step 2 (schemas, JSON config, difficulty in the prompt, print loop) and pastes the code and output for review.
2. Confirm the Step 1 commit and push worked.
3. Step 3: FastAPI endpoint.

## 12. Open questions ⚠️
- Did the Step 1 `git push` succeed (is `scratch.py` on GitHub)? Unconfirmed.
- Is the Step 0 push (`.gitignore`, `main.py`, `requirements.txt`) visible on GitHub? Unconfirmed.

## 13. Re-attach checklist
- [ ] `scratch.py`: it is in the project folder; the new chat can read it if opened in that folder. If not, paste it.

---
<sub>Audit: 13/13 sections · 5 rules · 4 corrections · 10 data points · secrets removed: none found (the exposed key was never copied here) · generated by active-memory</sub>
