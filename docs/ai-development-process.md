# AI-Assisted Development Process

## Course Requirement Fit

The ENTI 633 final project requires a working software application developed primarily using AI-assisted development tools. This project should be presented as both a software product and a learning journey about building with AI.

## Tools Used

| Tool | Used For | Evidence To Include |
|---|---|---|
| OpenAI Codex | Repository audit, branch implementation, documentation support, test/runnability checks | `docs/images/ai-coding-session-1.png`, related branch/commits |
| Cursor / Replit / Lovable / Bolt / v0 / other specialized AI coding tool | Main AI coding environment if used by group members | Screenshot of prompts and generated code review |
| ChatGPT / Claude / Gemini | Ideation, requirements, prompt refinement, blog drafting, debugging | Prompt examples and revision notes |
| Teachable Machine | Browser-side gesture/image model | Screenshot of classes/training/export |

## Why This Satisfies The Course Requirement

The repository documents a specialized AI-assisted development workflow rather than only generic chatbot copy-paste. Codex was used inside the development environment to inspect files, propose targeted changes, revise implementation details, improve documentation, run checks, and audit course compliance. The team should add screenshots from any other specialized coding environment used by group members so the final evidence package is complete.

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

## Evidence Still Needed

- Screenshots of actual AI coding sessions.
- Screenshot evidence for at least three representative prompts.
- A screenshot-backed before/after example showing how the team revised AI output.
- A short reflection from each team member, or one group reflection with named contributions.
