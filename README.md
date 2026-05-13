# Enti-Final-Project

## Run Case Mirror locally

Start the backend:

```bash
cd "casecoach/backend"
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend from the repo root:

```bash
python3 -m http.server 4173
```

Then open:

```text
http://localhost:4173/
```

The repo-root page redirects to `case-mirror/`. Camera and microphone features only work from `localhost` or HTTPS, not by opening the HTML file directly.
