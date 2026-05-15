# Demo Script

Use this 2-3 minute flow for the final presentation and narrated walkthrough.

## Setup Before Recording

- Start backend on `http://127.0.0.1:8000`.
- Start frontend on `http://localhost:4173/`.
- Confirm `curl http://localhost:8000/health` returns `{"ok":true}`.
- Prepare a short sample case prompt, rubric, recommendation, and slide outline.
- Decide whether webcam will be used. If camera permissions are risky, use typed-answer fallback and mention webcam as optional.

## Script

### 0:00-0:20 - Problem

"Case teams often practice their slides but do not get enough realistic judge Q&A before presenting. Case Mirror helps teams rehearse the hard part: defending the recommendation against rubric-aware questions and follow-ups."

### 0:20-0:45 - Setup

Open the setup page and paste the sample case materials. Point out that the app uses the case prompt, judging criteria, recommendation, context, and slide notes.

### 0:45-1:10 - Brief

Generate the brief. Show the problem summary, priorities, risks, and critique. Explain that this gives the team a quick mirror before Q&A.

### 1:10-1:45 - Q&A

Open rehearsal. Answer one judge-style question using typed input. If safe, enable camera and mention Teachable Machine gesture evidence. If not, say the app is designed to remain usable without camera/mic permissions.

### 1:45-2:25 - Report

Generate the final report. Highlight:

- strongest answer
- weakest answer
- missed criteria
- delivery/body evidence
- next practice drills

### 2:25-2:55 - AI-Assisted Development

"We built this with AI-assisted development tools for ideation, requirements, code generation, debugging, testing, and documentation. We also revised AI outputs so the app avoids unsafe claims like emotion or personality detection."

### 2:55-3:00 - Close

"Case Mirror is not an official judge. It is a practice tool that helps teams find weak assumptions before judges do."

## Backup Plan

If backend API keys fail, use the deterministic fallback and say:

"For demo reliability, the app has a local fallback. In production, configured model providers add richer market context and report synthesis."
