# Case Mirror / CaseCoach

Case Mirror is a university final project for a Generative AI and Prompting course. It helps student teams rehearse for case competitions by turning their case prompt, judging criteria, recommendation, and supporting materials into a focused practice flow.

The repository currently contains two connected parts:

- `case-mirror/`: static frontend for the user-facing rehearsal experience
- `casecoach/backend/`: FastAPI backend for upload, analysis, reporting, and live practice support

## What the product does

Case Mirror is built around a practical case competition workflow:

1. Teams paste the case prompt, judging rubric, recommendation, and optional context.
2. The app generates a case brief and critique.
3. Teams rehearse judge-style Q&A with adaptive follow-up questions.
4. The app produces a readiness report with strengths, weak spots, missed criteria, and next practice steps.

The backend also supports a deeper media-analysis pipeline for uploaded presentation videos and slide decks. That path adds transcript analysis, slide extraction, timestamped feedback, and observable delivery/body metrics with explicit safety limits.

The current live rehearsal flow now also includes a browser-side Teachable Machine image model for gesture and upper-body movement classification. That model runs locally in the browser and feeds evidence such as open palms, neutral hands, pointing, arms crossed, hands too low, excessive movement, and one-hand emphasis into the final readiness report.

## Repository Structure

```text
.
|- case-mirror/
|  |- index.html
|  |- app.js
|  |- styles.css
|  |- assets/teachable-image/
|  `- assets/images/
|
|- casecoach/
|  `- backend/
|     |- app/
|     |  |- api/
|     |  |- extractors/
|     |  |- models/
|     |  |- pipelines/
|     |  |- prompts/
|     |  |- scoring/
|     |  `- storage/
|     |- tests/
|     |- README.md
|     `- RUN_LIVE.md
|
|- index.html
`- vercel.json
```

## Frontend Overview

The frontend is a static HTML/CSS/JS app served from `case-mirror/`.

Main pages in the current flow:

- `Home`: product positioning and visual overview
- `Setup`: case prompt, rubric, recommendation, and optional context
- `Brief`: generated case brief and critique
- `Q&A`: judge-style rehearsal with typed fallback, microphone, and optional webcam preview
- `Report`: final readiness report

Key frontend characteristics:

- Vanilla JavaScript with hash-based routing
- Local session persistence via `localStorage`
- Static hosting friendly
- Strong typed-answer fallback for demo reliability
- Browser-side Teachable Machine gesture classification plus MediaPipe/body-motion sampling
- Safety language embedded in the UI

## Backend Overview

The backend is a FastAPI app under `casecoach/backend/`.

It supports two main modes:

- Uploaded presentation analysis:
  analyze recorded presentation video plus optional slide deck
- Live rehearsal support:
  generate live prep bullets, judge questions, and answer grading

Main backend responsibilities:

- ingest uploads
- persist jobs and artifact paths
- transcribe and preprocess media
- extract slides and observable metrics
- call external model providers
- score content, delivery, slides, and Q&A
- return report artifacts through JSON endpoints

## Local Development

### Frontend

From the repository root:

```bash
python3 serve_case_mirror.py
```

Open:

```text
http://localhost:4173/
```

The root page redirects to `case-mirror/`.

### Backend

From `casecoach/backend/`:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[test,slides,asr,body]"
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

### Environment

See:

- [casecoach/backend/.env.example](./casecoach/backend/.env.example)
- [casecoach/backend/API_KEYS.md](./casecoach/backend/API_KEYS.md)

Optional integrations currently referenced in the backend:

- Qwen-compatible reasoning endpoint for prep and answer grading
- Groq-compatible endpoint for live report synthesis
- Tavily for market-context research
- Deepgram for live transcription fallback
- MediaPipe/OpenCV for observable body metrics in the upload pipeline

Browser-side live rehearsal also depends on:

- Teachable Machine image model assets in `case-mirror/assets/teachable-image/`
- `@teachablemachine/image` loaded in `case-mirror/index.html`

## Deployment Notes

- `vercel.json` points the deployable output directory at `case-mirror/`
- The frontend is static and can be hosted independently
- Camera and microphone features need `localhost` or HTTPS
- Backend deployment should keep API keys on the server side only

## Safety and Scope

This project is a practice and coaching tool, not an official judging engine.

The system is designed to avoid:

- winner prediction
- official judge simulation claims
- protected-trait inference
- emotion or personality analysis
- unsupported body-language conclusions

Observable delivery/body signals are framed as coaching proxies, not psychological or identity judgments.

## Documentation

Additional project documentation lives in `docs/`:

- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- [docs/FRONTEND_GUIDE.md](./docs/FRONTEND_GUIDE.md)
- [docs/API_OVERVIEW.md](./docs/API_OVERVIEW.md)

## Current State

This repository is already beyond a blank MVP. The frontend has a polished landing page and guided rehearsal flow, and the backend includes both offline analysis and live practice endpoints. The main documentation gap was project structure and onboarding clarity, which this README and the `docs/` folder are intended to fix.
