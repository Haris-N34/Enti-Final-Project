# Demo Readiness Plan

This file documents the safest final demo path for the ENTI 633 final project.
It is written for the final presentation, video walkthrough, and last-minute QA
so the team can show a working product without depending on fragile browser
permissions or production-only services.

## Recommended Demo Mode

Use the deployed frontend for the safest static demo, or use the local frontend
plus local FastAPI backend for the full backend-supported workflow.

## Option A: Safest Demo, Static Frontend

Use this path when presentation time is limited or internet/browser permissions
are unreliable.

1. Open the deployed frontend: `https://enti-final-project.vercel.app/`.
2. Create or continue the local demo profile.
3. Click `Load sample case`.
4. Continue through setup.
5. Generate the case brief.
6. Practice judge-style Q&A using typed answers.
7. Skip microphone and camera if permissions are unreliable.
8. Generate the final readiness report.
9. Show strengths, weak spots, missed criteria, and next drills.

## Option B: Full Local Backend Demo

Use this path when the team wants to demonstrate the backend-supported AI/API
workflow from a local machine.

Start backend:

```bash
cd casecoach/backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start frontend from the repository root:

```bash
python3 serve_case_mirror.py
```

Open:

```text
http://localhost:4173/
```

Health check:

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"ok":true}
```

## 60-90 Second Demo Script

Case Mirror helps student case teams practice the judge-style Q&A they will face
after presenting.

We built it because teams often rehearse slides, but they do not always rehearse
how they will defend assumptions, risks, tradeoffs, and implementation details
under pressure.

For the demo, I will load a sample case so we can move quickly. The app turns the
case prompt, rubric, and recommendation into a structured brief, then generates
judge-style questions.

I can answer with text even if microphone or camera permissions fail, which makes
the demo reliable. After the Q&A, the final report summarizes strengths, weak
spots, missed criteria, and concrete drills for the next practice round.

This is practice feedback only. It is not official judging, winner prediction,
emotion analysis, or personality scoring.

## Demo Risks And Backups

| Risk | Backup |
|---|---|
| Backend unavailable | Use deterministic frontend fallback and static demo mode |
| Microphone permission fails | Use typed answers |
| Webcam permission fails | Continue without delivery signals |
| Internet is slow | Use local frontend and sample case |
| Teachable Machine CDN unavailable | Skip camera and show the report without body evidence |
| API keys are unavailable | Use fallback warnings and local-safe outputs |
| Time is short | Use sample case and skip optional permissions |

## Final Demo Checklist

- Landing page loads.
- Local demo profile can be created or continued.
- Sample case loads.
- Setup form validates required fields.
- Brief page generates.
- Q&A page appears.
- Typed answer can be entered.
- Follow-up or skip controls work.
- Final report generates.
- Camera denied state does not block the typed workflow.
- Microphone denied state does not block the typed workflow.
- The presenter can explain that this is a course MVP, not a production SaaS
  product.
