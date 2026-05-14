# API Overview

## Purpose

The backend API supports two related experiences:

- asynchronous uploaded-presentation analysis
- synchronous or near-live rehearsal support

The API is intentionally practical for an MVP. It favors clear JSON payloads and artifact retrieval over deep orchestration complexity.

## Base Backend

Backend entry point:

- [casecoach/backend/app/main.py](../casecoach/backend/app/main.py)

Health endpoint:

- `GET /health`

## Upload and Analysis Endpoints

### `POST /api/upload`

Purpose:

- accept a presentation video
- optionally accept a slide deck
- capture case prompt and rubric metadata
- create a backend job record

Important request fields:

- `video_file`
- `slide_deck`
- `case_prompt`
- `rubric`
- `team_members`
- `presentation_length_limit_minutes`
- `qa_included`
- `analysis_mode`

Returns:

- `job_id`
- job status
- warnings

### `POST /api/analyze/{job_id}`

Purpose:

- queue or start analysis for an uploaded job

Returns:

- current status
- confirmation message

### `GET /api/status/{job_id}`

Purpose:

- poll job state while analysis is running

Possible states include:

- `uploaded`
- `preprocessing`
- `transcribing`
- `extracting_slides`
- `reasoning`
- `scoring`
- `completed`
- `failed`

## Report Artifact Endpoints

### `GET /api/report/{job_id}`

Returns the main generated report artifact.

### `GET /api/timeline/{job_id}`

Returns timeline-aligned analysis events.

### `GET /api/slides/{job_id}`

Returns extracted slide-level outputs.

### `GET /api/transcript/{job_id}`

Returns transcript segments and warnings.

### `GET /api/body-metrics/{job_id}`

Returns observable body-metric artifacts when available.

### `GET /api/export/json/{job_id}`

Returns JSON export of the report artifact.

## Live Rehearsal Endpoints

Defined in:

- [casecoach/backend/app/api/routes_live.py](../casecoach/backend/app/api/routes_live.py)

### `POST /api/live/prepare`

Purpose:

- generate live prep bullets from the current case materials
- summarize slide text
- provide likely judge questions
- optionally include market context from Tavily-backed research

Request fields:

- `company`
- `industry`
- `case_prompt`
- `slide_text`
- `presentation_minutes`

Response fields:

- `slide_summary`
- `market_context`
- `market_sources`
- `likely_judge_questions`
- `warnings`

### `POST /api/live/grade-answer`

Purpose:

- grade a single live answer
- combine text, case context, slide text, and observable metrics
- accept browser-side Teachable Machine gesture summaries alongside other delivery metrics
- return an adaptive follow-up question

Request fields:

- `question`
- `answer`
- `slide_text`
- `case_prompt`
- `market_context`
- `market_sources`
- `metrics`
- `elapsed_seconds`

Response fields:

- `content_score`
- `clarity_score`
- `evidence_score`
- `delivery_score`
- `metrics`
- `feedback`
- `follow_up_question`
- `warnings`

### `POST /api/live/report`

Purpose:

- persist a full live rehearsal evidence bundle
- write `evidence.json`, `body_events.jsonl`, compatibility `gesture_events.jsonl`, and `report.json`
- generate a tangible readiness report from saved transcript, answer scores, follow-ups, and body-positioning/Teachable movement metrics
- fall back to deterministic evidence-specific reporting when the report model is unavailable

Important request fields:

- `session_id`
- `evidence_bundle` using `live_evidence_v2`
- `answers`
- `body_events`
- `body_summary`
- `body_quality_warnings`
- `body_metrics_version`
- `gesture_events`
- `gesture_summary`
- `local_report`

Response fields:

- `report`
- `warnings`

### `POST /api/live/deepgram-token`

Purpose:

- mint a short-lived Deepgram browser token when configured

### `WS /api/live/deepgram-proxy`

Purpose:

- proxy browser audio to Deepgram when direct token usage is not the chosen path

## Safety Expectations

The API is built around strict framing:

- no winner prediction
- no official judging claims
- no personality analysis
- no emotion detection
- no protected-trait inference

Observable signals such as filler words, transcript pacing, and pose stability are acceptable only when returned as narrow coaching proxies.

## Environment Dependencies

Relevant environment variables are documented in:

- [casecoach/backend/.env.example](../casecoach/backend/.env.example)
- [casecoach/backend/API_KEYS.md](../casecoach/backend/API_KEYS.md)

Key optional providers currently referenced:

- Qwen-compatible reasoning endpoint for prep and answer grading
- Groq-compatible endpoint for live report synthesis
- Tavily research API
- Deepgram transcription
- MediaPipe/OpenCV body-tracking stack for upload analysis

Important browser-side live inputs that are not server-hosted providers:

- Teachable Machine image model loaded from `case-mirror/assets/teachable-image/`
- MediaPipe pose and face sampling in the browser
- local body event aggregation in the frontend before `POST /api/live/report`
