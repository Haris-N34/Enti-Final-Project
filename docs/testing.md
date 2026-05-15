# Testing And QA

Latest QA pass: May 15, 2026.

Environment used for this pass:

| Item | Value |
|---|---|
| Machine | Local macOS development machine |
| OS | macOS 26.3.1, build 25D2128 |
| Browser | Codex in-app browser against local frontend |
| Frontend Python | Python 3.14.3 for `serve_case_mirror.py` |
| Backend Python | Python 3.12.13 from `casecoach/backend/.venv` |
| Node | v22.22.1 |
| Frontend URL | `http://127.0.0.1:4173/case-mirror/` |
| Backend URL | `http://127.0.0.1:8000` |
| Deployed frontend smoke URL | `https://enti-final-project.vercel.app/` |

## Command Results

Run from the repository root unless noted.

| Check | Command | Result | Output |
|---|---|---|---|
| Frontend syntax | `node --check case-mirror/app.js` | PASS | No output; exit code 0 |
| Python helper syntax | `python3 -m py_compile serve_case_mirror.py` | PASS | No output; exit code 0 |
| Backend tests | `cd casecoach/backend && .venv/bin/python -m pytest -q` | PASS | `18 passed in 0.13s` |
| Local frontend root | `curl -i http://127.0.0.1:4173/` | PASS | Returned `HTTP/1.0 200 OK` and `Cache-Control: no-store` |
| Local frontend app path | `curl -i http://127.0.0.1:4173/case-mirror/` | PASS | Returned `HTTP/1.0 200 OK` |
| Backend health | `curl -i http://127.0.0.1:8000/health` | PASS | Returned `HTTP/1.1 200 OK` and `{"ok":true}` |
| Deployed frontend root | `curl -I https://enti-final-project.vercel.app/` | PASS | Returned `HTTP/2 200` |
| Markdown table audit | Local script over `README.md` and `docs/*.md` | PASS | `potential table issues: 0` |

Backend and frontend servers were started locally with:

```bash
cd casecoach/backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```bash
python3 serve_case_mirror.py
```

## Backend API Smoke Test

The live API was exercised with sample EcoRide case data.

| Endpoint | Result | Notes |
|---|---|---|
| `POST /api/live/prepare` | PASS | Returned `likely_judge_questions`, `market_context`, `market_sources`, `slide_summary`, and `warnings`. Warnings were substantive model notes about missing financial and operational evidence, not transport failures. |
| `POST /api/live/grade-answer` | PASS with safety fallback | Returned content, clarity, evidence, and delivery scores. The model response triggered the safety fallback because unsupported confidence language was detected, so deterministic grading was used. |
| `POST /api/live/report` | PASS | Returned a shaped report with score fields and no warnings in the API smoke test. |

## Browser Demo Flow

The local app was tested in the Codex in-app browser at `http://127.0.0.1:4173/case-mirror/`.

| Flow Step | Result | Evidence From Manual Browser Check |
|---|---|---|
| Landing page | PASS | Page loaded and showed Case Mirror positioning, local profile link, start controls, and sample-case entry point. |
| Local profile | PASS | Created a local demo profile with name and email. |
| Load sample case | PASS | Sample EcoRide case, rubric, recommendation, industry context, constraints, and slide outline populated the setup form. |
| Setup validation path | PASS | Required setup fields were present and filled before brief generation. |
| Brief generation | PASS | Backend-generated brief loaded with problem summary, market pressure points, difficult questions, judge priorities, strengths, gaps, assumptions, and risks. |
| Q&A rehearsal | PASS | Rehearsal page loaded with `Question 1 of 5`, typed answer box, skip controls, microphone button, and optional camera panel. |
| Typed answer | PASS | A typed answer saved successfully and was graded by the backend path. |
| Follow-up | PASS | One adaptive follow-up appeared, the answer box cleared for the follow-up, and the follow-up answer saved. |
| Skip question | PASS | Questions 2 through 5 were skipped successfully using the skip button. |
| Final report | PASS | Backend-generated report loaded with scores, strengths, risks, tangible improvements, body-movement notice, weak criteria, weak assumptions, missing metrics, best answer, weakest answer, and improved answer suggestions. |
| Camera fallback | PASS with limitation | The full typed rehearsal and report flow completed without enabling camera preview. The report correctly stated that no webcam body samples were captured. Explicit OS/browser camera-denial permission prompts were not re-tested in this automated pass. |
| Microphone fallback | PASS with limitation | The full typed rehearsal and report flow completed without using microphone transcription. Explicit OS/browser microphone-denial permission prompts were not re-tested in this automated pass. |

## Evidence File Check

The backend wrote live rehearsal evidence artifacts under `casecoach/backend/data/live_sessions/` during local/API smoke tests. The generated files include:

| Artifact | Purpose |
|---|---|
| `evidence.json` | Normalized rehearsal inputs, answers, scores, and body evidence summary before report synthesis |
| `body_events.jsonl` | Raw timestamped body/pose/Teachable observations when captured |
| `gesture_events.jsonl` | Compatibility alias for older report paths |
| `report.json` | Final backend-generated report artifact |

These runtime data files are local artifacts and are not part of the submitted source evidence unless intentionally exported.

## Known Limitations

| Area | Limitation |
|---|---|
| Deployed frontend | The deployed static frontend is the safest public demo entry point. The backend is local-only for this MVP unless a separate backend host is configured and verified. |
| Live model providers | Remote model behavior depends on valid API keys and provider availability. The app has deterministic fallback paths for grading/reporting when model output is unavailable or unsafe. |
| Camera and microphone | Typed-answer rehearsal is the reliable demo path. Webcam, Teachable Machine, and microphone features depend on browser permissions, lighting, camera availability, CDN/model loading, and local device support. |
| Customer discovery evidence | Slide-backed ENACTUS/JDC validation summaries are now documented. Full interview transcripts, participant names, and exact interview dates are not included. |
| AI coding screenshots | Requested screenshot files such as `docs/images/ai-coding-session-1.png` and prompt screenshots were not present in `docs/images/` during this QA pass, so documentation should not claim they are included. |
| Main-branch merge | This pass does not merge to `main`. Merge only after the team confirms the docs render correctly, pending blog/video links are acceptable, and this is the intended D2L branch. |

## Final Manual Checklist

Use this checklist immediately before recording the walkthrough video or submitting the final D2L package.

| Item | Status From Latest Pass |
|---|---|
| Landing page loads | PASS locally |
| Local profile can be created | PASS locally |
| Sample case loads | PASS locally |
| Setup form accepts required fields | PASS locally |
| Brief page generates | PASS locally |
| Q&A page appears | PASS locally |
| Typed answer can be entered and saved | PASS locally |
| Follow-up or skip controls work | PASS locally |
| Final report generates | PASS locally |
| Camera-disabled typed fallback works | PASS with limitation |
| Microphone-disabled typed fallback works | PASS with limitation |
| Deployed frontend reachable | PASS by HTTP smoke check |
