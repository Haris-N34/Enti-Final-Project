# CaseCoach Backend

Backend-only MVP for Case Mirror video-model analysis.

## Runtime Requirements

- Python 3.12. The package intentionally pins `>=3.12,<3.13` because current video/ML packages lag newer Python releases.
- `ffmpeg` and `ffprobe` on `PATH`.
- A remote OpenAI-compatible Qwen3-VL endpoint for model reasoning, configured with `QWEN_VL_BASE_URL` and `QWEN_VL_API_KEY`.

The backend can still run without Qwen configuration, but model reasoning sections will return warnings and deterministic fallback feedback.
Body posture tracking uses open-source MediaPipe Pose and OpenCV when installed. Without those packages, the backend still runs and returns a clear warning in the report.

## Quick Start

```bash
cd casecoach/backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[test,slides,asr,body]"
uvicorn app.main:app --reload
```

For a minimal install without optional local ASR/PDF support:

```bash
pip install -e ".[test]"
```

## Environment Variables

```bash
CASECOACH_DATA_DIR=./data
DATABASE_URL=sqlite:///./data/casecoach.sqlite3
QWEN_VL_BASE_URL=
QWEN_VL_API_KEY=
QWEN_VL_MODEL=qwen3.6-plus
QWEN_OMNI_BASE_URL=
QWEN_OMNI_API_KEY=
QWEN_OMNI_MODEL=Qwen/Qwen3-Omni-30B-A3B-Thinking
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_API_KEY=
GROQ_MODEL=gpt-oss-120b
ASR_PROVIDER=faster_whisper
ASR_MODEL=base
MAX_UPLOAD_MB=1024
TAVILY_API_KEY=
```

## API

- `POST /api/upload`
- `POST /api/analyze/{job_id}`
- `GET /api/status/{job_id}`
- `GET /api/report/{job_id}`
- `GET /api/timeline/{job_id}`
- `GET /api/slides/{job_id}`
- `GET /api/transcript/{job_id}`
- `GET /api/body-metrics/{job_id}`
- `GET /api/export/json/{job_id}`

## Safety Principle

The backend separates observable metrics from interpretation. It must not infer protected traits, emotion, personality, official judging outcomes, or winner likelihood. Feedback should stay grounded in timestamps, transcript text, slide content, and computed metrics.
