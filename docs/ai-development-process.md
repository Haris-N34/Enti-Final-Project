# AI-Assisted Development Process

## Course Requirement Fit

The ENTI 633 final project requires a working software application developed primarily using AI-assisted development tools. This project should be presented as both a software product and a learning journey about building with AI.

## Tools Used

| Tool / System | Used For | Evidence |
|---|---|---|
| OpenAI Codex | Repository audit, documentation improvement, grading-readiness checks, QA evidence updates, and branch implementation support | Current branch commits; final deck slide 9 says the product was built using Codex |
| ChatGPT / Claude / Gemini or equivalent general AI tools | Ideation, requirements framing, prompt refinement, writing revision, and debugging support | Representative prompt examples in `prompt-examples.md`; final deck slide 10 describes AI help with ideation, requirements, development, and writing |
| FastAPI backend with model/provider integrations | API-based AI workflow for preparation, grading, report generation, and media-analysis support | Backend code, API docs, testing evidence |
| Google Teachable Machine | Browser-side delivery/gesture evidence in the MVP | Teachable Machine model assets in `case-mirror/assets/teachable-image/`; final deck slide 9 |
| Tavily / Deepgram / Qwen-compatible reasoning endpoint | Optional external services for research, transcription fallback, and reasoning support | Backend docs and final deck slide 9 |
| Vercel + GitHub | Static frontend deployment and public documentation | README, Vercel config, deployment URL, GitHub docs |

## Why This Satisfies The Course Requirement

The project was developed through a specialized AI-assisted workflow rather than only by copying generic chatbot output into a compiler. The final presentation deck states that the product was built using Codex, and the repository contains branch commits where Codex-assisted work improved documentation, QA evidence, course-readiness mapping, and repository structure.

AI also supported the broader development lifecycle: narrowing the idea, defining requirements, separating MVP scope from future scope, scaffolding frontend/backend work, and improving documentation. Human review remained central. The team removed unsupported traction claims, constrained body/delivery language, avoided winner prediction and personality/emotion claims, and manually tested the setup → brief → Q&A → report flow.

## Slide-Backed AI Development Narrative

The final presentation describes AI as a development partner across four areas:

| Area | How AI Helped | Human Oversight |
|---|---|---|
| Ideation | Narrowed a broad presentation-coaching idea into a focused rehearsal tool | Team selected the case-competition wedge and rejected generic positioning |
| Requirements | Defined the four-step flow and separated MVP from advanced features | Team kept the MVP limited to setup, brief, Q&A, feedback, and report |
| Development | Helped scaffold frontend pages, FastAPI routes, and backend structure | Team tested the actual workflow and kept fallback paths for demo reliability |
| Writing | Converted scattered project details into clearer GitHub documentation | Team checked that claims matched the actual repo and app |

## Verified Repository Evidence

| Evidence | Location | What It Proves |
|---|---|---|
| Course-compliance audit and documentation revision | Current Codex branch commits and documentation updates | AI-assisted repository setup, audit, and documentation improvement |
| Prompt examples | [prompt-examples.md](./prompt-examples.md) | Representative prompts used or adapted during development |
| Safety and scope documentation | [limitations-and-future-work.md](./limitations-and-future-work.md), backend tests | Human review of AI output boundaries |
| Development iteration | [development-log.md](./development-log.md) | Multiple commits across UI, backend, model integration, deployment, and QA |

The remaining high-value evidence is screenshots from the exact AI coding environment used by the team for main development.

## Workflow

1. Ideation: identify a business education problem where AI assistance could produce practical value.
2. Requirements: convert the problem into must-have user stories, constraints, and safety boundaries.
3. Prototype: create a static frontend flow that can be demoed reliably.
4. Backend: build FastAPI endpoints for upload, live prep, grading, reporting, and provider integrations.
5. AI/model features: add AI-assisted brief generation, judge-style questions, report synthesis, and Teachable Machine gesture evidence.
6. Review: run tests, inspect code, remove overclaims, and add safety language.
7. Documentation: create README, architecture docs, requirements docs, prompt examples, and submission planning materials.

## What AI Helped With

- Generating first-pass code structures.
- Creating endpoint and schema patterns.
- Drafting explanatory documentation.
- Finding grading risks in the repository.
- Suggesting testing and demo workflows.
- Improving phrasing around safety and privacy.

## What Humans Reviewed Or Revised

- Product scope and target use case.
- Which AI outputs matched the actual app.
- Safety boundaries around body/delivery feedback.
- Which features should be demoed versus described as future scope.
- Any prompt output before it became documentation or code.
- Final claims in the README, blog, and presentation.

## AI Mistakes And Corrections To Discuss

Use this section in the blog and presentation.

- AI can overclaim implementation status; the team should verify every feature in the app.
- AI can write generic business justification; the team should add real user interviews.
- AI can generate broad "confidence" or body-language claims; the team constrained outputs to observable coaching evidence.
- AI can create large files quickly; the team should explain why the static MVP accepted some frontend file size tradeoffs.

## Example Of Human Review And Revision

| AI Output / Initial Draft | Human Review Concern | Final Decision |
|---|---|---|
| Broad delivery or confidence language | Could imply emotion/personality inference or official judging | Rewrote as observable delivery signals only |
| Generic presentation-coach positioning | Too broad and crowded | Narrowed product to case-competition Q&A rehearsal |
| Ambitious production features | Too much for course MVP | Kept static frontend, local backend, typed fallback, and report flow |
| Market or traction claims | Unsupported without evidence | Removed or reframed as MVP/demo language |

## Evidence Status

| Evidence Item | Status | Note |
|---|---|---|
| Codex use | Documented | Final deck says the product was built using Codex; branch commits show Codex-assisted repo-readiness work |
| Representative prompts | Documented as text | `prompt-examples.md` includes prompts and human revision notes |
| Prompt screenshots | Not included in repo unless files are added | Required mainly for the blog/article evidence package; do not claim screenshots exist unless files are present |
| Teachable Machine evidence | Partially documented | Model assets are in the repo; add a screenshot only if available |
| Human review and revision | Documented | Safety boundaries, scope control, QA, and removal of unsupported claims are documented |
