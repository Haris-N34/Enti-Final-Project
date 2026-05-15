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
- Deployment smoke test still needs a final public URL.

## Final QA Evidence To Add

| Test | Browser / Environment | Date | Result | Notes |
|---|---|---|---|---|
| Local frontend run | TODO | TODO | TODO | TODO |
| Backend health check | TODO | TODO | TODO | TODO |
| Full demo flow | TODO | TODO | TODO | TODO |
| Camera denied fallback | TODO | TODO | TODO | TODO |
| Final video rehearsal | TODO | TODO | TODO | TODO |
