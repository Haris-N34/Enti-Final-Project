# Testing And QA

## Automated Backend Tests

Run from `casecoach/backend`:

```bash
.venv/bin/python -m pytest -q
```

Latest local audit result:

```text
18 passed
```

Covered areas include:

- body tracking metrics
- delivery scoring
- upload ingest validation
- job storage
- live report evidence handling
- Qwen client behavior
- safety language constraints

## Local Run Smoke Test

Start backend:

```bash
cd casecoach/backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Check backend:

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"ok":true}
```

Start frontend:

```bash
python3 serve_case_mirror.py
```

Open:

```text
http://localhost:4173/
```

## Manual Demo QA Checklist

Complete before final video and presentation:

- Landing page loads from `http://localhost:4173/`.
- Root page redirects to `case-mirror/`.
- Setup form accepts case prompt, rubric, recommendation, and optional context.
- Brief generation works with backend available.
- Brief generation falls back gracefully if backend is unavailable.
- Rehearsal page shows judge-style question.
- Typed answer can be saved and graded.
- Follow-up question appears when appropriate.
- Skip question and skip follow-up controls work.
- Final report generates.
- Clear session works.
- Copy/export report works if used in demo.
- Webcam denied state does not block typed rehearsal.
- Microphone denied state does not block typed rehearsal.
- Teachable Machine model loads when camera is enabled and internet/CDN access is available.
- App remains usable on a laptop presentation resolution.

## Known Test Gaps

- No automated frontend browser tests yet.
- Full webcam/microphone behavior depends on browser permissions.
- Live model-provider paths require valid API keys.
- Deployed frontend works, but the backend is local-only for this MVP.
- Vercel serves the static app at `/`; `/case-mirror/` is not the deployed route because `case-mirror/` is configured as the output directory.

## QA Evidence

| Test | Browser / Environment | Date | Result | Notes |
|---|---|---|---|---|
| Backend automated tests | Python 3.12.5, local `.venv` | May 15, 2026 | PASS | `18 passed in 0.18s` |
| Frontend syntax check | Node `--check case-mirror/app.js` | May 15, 2026 | PASS | No syntax errors |
| Python helper syntax check | `python3 -m py_compile serve_case_mirror.py` | May 15, 2026 | PASS | No syntax errors |
| Local frontend run | `http://127.0.0.1:4173/` | May 15, 2026 | PASS | Returned `HTTP/1.0 200 OK` |
| Backend health check | `http://127.0.0.1:8000/health` | May 15, 2026 | PASS | Returned `{"ok":true}` |
| Live prepare endpoint | `POST /api/live/prepare` | May 15, 2026 | PASS with fallback | Returned judge questions and warnings for missing optional API keys |
| Live answer grading endpoint | `POST /api/live/grade-answer` | May 15, 2026 | PASS with fallback | Returned scores, feedback, and follow-up question |
| Deployed frontend root | `https://enti-final-project.vercel.app/` | May 15, 2026 | PASS | Returned `HTTP/2 200` |
| Deployed frontend assets | `/app.js`, `/styles.css` | May 15, 2026 | PASS | Both assets returned `HTTP/2 200` |
| Browser demo flow | Deployed frontend in browser | May 15, 2026 | PASS | Completed local profile, setup, brief, Q&A, and report flow |
| Camera denied fallback | Browser demo flow without camera | May 15, 2026 | PASS | Typed-answer path remained usable without camera |

## Final Pre-Submission QA

Run this checklist immediately before recording the walkthrough video,
presenting, or submitting the D2L deliverable.

| Test | Browser / Environment | Date | Result | Notes |
|---|---|---|---|---|
| Backend automated tests | Python 3.12.5, local `.venv` | May 15, 2026 | PASS | `.venv/bin/python -m pytest -q` returned `18 passed` |
| Frontend syntax check | Node `--check case-mirror/app.js` | May 15, 2026 | PASS | No syntax errors |
| Python helper syntax check | `python3 -m py_compile serve_case_mirror.py` | May 15, 2026 | PASS | No syntax errors |
| Local backend health check | Local FastAPI backend | May 15, 2026 | PASS | `curl http://localhost:8000/health` returned `{"ok":true}` |
| Deployed frontend smoke check | Vercel static frontend | May 15, 2026 | PASS | `curl -I https://enti-final-project.vercel.app/` returned `HTTP/2 200` |
| Risky copy scan | Repository text search | May 15, 2026 | PASS | No leftover unsupported traction strings or merge markers found |

## Final Manual Browser QA Checklist

- Landing page loads from the deployed frontend.
- Local profile can be created or continued.
- `Load sample case` works.
- Setup form validates required fields.
- Brief page generates.
- Q&A page appears.
- Typed answer can be entered.
- Follow-up or skip controls work.
- Final report generates.
- Camera denied state does not block typed rehearsal.
- Microphone denied state does not block typed rehearsal.
- The app copy frames pricing as a proposed MVP model, not a live commercial
  product.
