# Run Live Presentation Practice

This starts the backend on `localhost:8000` and the static live rehearsal page on `localhost:4173`.

## 1. Install backend runtime

Use Python 3.12 if available.

```bash
cd "/Users/arashajdari/AI COURSE 333/casecoach/backend"
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[test,slides,asr]"
```

If Python 3.12 is not installed yet:

```bash
brew install python@3.12 ffmpeg
```

## 2. Confirm `.env`

The backend already has a local `.env` file. It is gitignored and should contain:

```bash
QWEN_VL_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_VL_API_KEY=...
QWEN_VL_MODEL=qwen3.6-plus
```

Optional current market research:

```bash
TAVILY_API_KEY=...
```

Optional live transcription:

```bash
DEEPGRAM_API_KEY=...
```

## 3. Start backend

```bash
cd "/Users/arashajdari/AI COURSE 333/casecoach/backend"
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Check:

```bash
curl http://localhost:8000/health
```

## 4. Start the live page

In a second terminal:

```bash
cd "/Users/arashajdari/AI COURSE 333"
python3 -m http.server 4173
```

Open:

```text
http://localhost:4173/case-mirror/live.html
```

## 5. Live workflow

1. Paste the case prompt.
2. Paste slide titles, slide bullets, or speaker notes into `Slide text / speaker notes`.
3. Click `Prepare questions`.
4. Click `Enable camera` if you want a preview.
5. Click `Start answering`.
6. Speak your answer.
7. Click `Stop and grade`.
8. Use the adaptive follow-up question for the next practice answer.

## Current limitations

- Live page reads text-based slide exports now. PDF/PPTX rendering is handled by the backend upload pipeline, not the live browser page.
- Market context uses Tavily when `TAVILY_API_KEY` is configured, then Qwen turns those snippets into prep bullets and judge questions.
- Real-time tracking uses Deepgram when `DEEPGRAM_API_KEY` is configured. The browser first tries a short-lived Deepgram token, then a backend WebSocket proxy, then browser speech recognition or manual transcript text.
- Body metrics are browser-side MediaPipe/motion proxies. They are observable coaching signals, not emotion/personality detection.
