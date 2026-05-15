# Contributing

This repository is a course project, so contributions should prioritize demo reliability, documentation clarity, and honest scope over adding unfinished features.

## Local Setup

Start the frontend:

```bash
python3 serve_case_mirror.py
```

Start the backend:

```bash
cd casecoach/backend
python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[test,slides,asr,body]"
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Checks Before Committing

Run:

```bash
cd casecoach/backend
.venv/bin/python -m pytest -q
```

From the repository root:

```bash
node --check case-mirror/app.js
python3 -m py_compile serve_case_mirror.py
```

Smoke-check:

```bash
curl http://localhost:8000/health
```

## Documentation Rules

- Keep README claims aligned with features that can be demonstrated.
- Use `docs/` for evidence, architecture, requirements, testing, and process notes.
- Add real screenshots under `docs/images/`.
- Do not invent customer interviews, prompt screenshots, team details, or deployment links.
- Mark future work as future work instead of describing it as complete.

## Safety Rules

- Do not add emotion, personality, protected-trait, or winner-prediction claims.
- Keep body and gesture metrics framed as observable coaching proxies.
- Never commit `.env` files or real API keys.
- Keep the local demo profile clearly labeled as local-only, not production authentication.
