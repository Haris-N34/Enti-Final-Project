# Architecture

## System Summary

Case Mirror / CaseCoach is split into a static frontend and a FastAPI backend.

- The frontend handles the user workflow, local session state, and browser capabilities such as microphone and webcam preview.
- The frontend also runs the live Teachable Machine classifier and browser-side body sampling during rehearsal.
- The backend handles file upload, analysis jobs, report artifacts, live rehearsal prep, and model-provider integration.

This split is appropriate for the project because the user-facing flow must stay lightweight and demo-friendly, while the heavier media and model work can remain server-side.

## High-Level Components

### Frontend: `case-mirror/`

Core files:

- `index.html`
- `styles.css`
- `app.js`
- `assets/images/`
- `assets/teachable-image/`

Responsibilities:

- render the landing page and all app screens
- manage hash-based routing
- persist the current working session in `localStorage`
- collect text inputs for case setup
- display generated brief, rehearsal prompts, and final report
- provide typed answer fallback
- optionally use browser microphone and webcam APIs
- load the Teachable Machine image classifier in the browser
- combine Teachable Machine classes with MediaPipe pose, face visibility, and frame-motion sampling
- write `bodyEvents` evidence into the local session for final report synthesis
- call live backend endpoints when available

### Backend: `casecoach/backend/`

Core areas:

- `app/api/`: HTTP and WebSocket routes
- `app/extractors/`: speech, search, model, and body-tracking integrations
- `app/models/`: shared schemas and rubric definitions
- `app/pipelines/`: orchestration for ingest, preprocess, analysis, and report building
- `app/scoring/`: scoring helpers by dimension
- `app/storage/`: job database and artifact storage
- `tests/`: backend tests

Responsibilities:

- accept uploaded presentation assets
- validate input types and limits
- create analysis jobs
- store metadata and artifact paths
- preprocess videos and slide decks
- extract transcripts, slide data, and observable metrics
- generate score/report artifacts
- support live rehearsal preparation and answer grading

## Main Workflows

### Workflow 1: Frontend Rehearsal Flow

1. User opens the static app.
2. User fills out case setup inputs.
3. `app.js` generates or requests a brief/critique flow.
4. User rehearses five judge questions and follow-ups.
5. User receives a readiness report.

This path is optimized for demo speed and reliability. Typed answers remain the baseline fallback if browser speech or camera access fails.

### Workflow 2: Uploaded Presentation Analysis

1. Client uploads a presentation video and optional slide deck to `POST /api/upload`.
2. Backend creates a job record and saves artifacts to disk.
3. Client triggers analysis with `POST /api/analyze/{job_id}`.
4. Backend pipeline runs transcription, slide extraction, body metrics, reasoning, and scoring.
5. Client polls `GET /api/status/{job_id}`.
6. Final report, transcript, slides, timeline, and export JSON are fetched from report endpoints.

### Workflow 3: Live Rehearsal Support

1. Frontend sends current case materials to `POST /api/live/prepare`.
2. Backend returns market context, prep bullets, and likely judge questions.
3. When the webcam is enabled, the frontend loads the local Teachable Machine model from `case-mirror/assets/teachable-image/` and samples gesture classes in the browser.
4. The frontend combines Teachable Machine outputs with MediaPipe pose, face visibility, and simple frame-difference motion signals into `bodyEvents` and `body_summary`.
5. During answer rehearsal, frontend sends a question, answer, and observable metrics to `POST /api/live/grade-answer`.
6. Backend returns content, clarity, evidence, and delivery feedback plus an adaptive follow-up question.
7. At the end of the session, the frontend sends the full evidence bundle to `POST /api/live/report`, where report synthesis can use both answer text and browser-captured body evidence.

## Data and State

### Frontend State

The frontend keeps a single active session in `localStorage`. This supports:

- quick restarts
- no-auth demo flow
- persistence across refreshes
- simple export/copy flows

### Backend State

The backend stores:

- job metadata in SQLite
- uploaded assets and generated artifacts on disk
- structured report outputs as JSON files
- live rehearsal evidence bundles that include Teachable Machine-derived body event summaries

This is intentionally practical for an MVP and easier to debug than a distributed or cloud-heavy setup.

## Safety Boundaries

The architecture explicitly separates observable metrics from interpretation.

Examples:

- delivery timing and filler counts are acceptable
- body posture stability and gesture-class proxies are acceptable when framed narrowly
- winner prediction, emotion detection, personality scoring, and protected-trait inference are not acceptable

These rules are enforced through prompt wording, output shaping, and safety tests in the backend.

## Why This Structure Works

This structure fits the course project well because it balances:

- demo polish
- technical realism
- AI-assisted features
- safety constraints
- rapid iteration

The frontend can evolve quickly without framework migration, and the backend can absorb more sophisticated analysis logic without bloating the browser app.
