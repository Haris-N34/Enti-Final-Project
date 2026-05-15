# Requirements

## Product Goal

Build a working AI-assisted case rehearsal application that helps student teams practice case competition Q&A and produce a readiness report before the final presentation.

## Functional Requirements

### Must Have

- Users can enter a case prompt, judging criteria, team recommendation, and optional context.
- The app generates a case brief that summarizes the problem, priorities, risks, and suggested story arc.
- The app generates judge-style practice questions.
- Users can answer questions with a reliable typed fallback.
- The app can generate follow-up questions when answers are weak or incomplete.
- The app produces a final readiness report with strengths, weak spots, missed criteria, and practice recommendations.
- The app works locally without requiring production deployment.
- The backend exposes a health endpoint and live practice endpoints.
- The project has clear documentation, setup instructions, and testing notes.

### Should Have

- Optional microphone support for spoken practice.
- Optional webcam support for visible delivery evidence.
- Browser-side Teachable Machine model for gesture/upper-body categories.
- Backend model-provider integration for richer prep, grading, and report synthesis.
- Deterministic local fallback when backend or API keys are unavailable.
- Export or copyable report output.

### Nice To Have

- Deployed frontend URL.
- Deployed backend URL.
- Full uploaded presentation video/deck analysis.
- More comprehensive frontend automated tests.
- Multi-user accounts and cloud persistence.
- Coach dashboard.

## Non-Functional Requirements

- Demo reliability: typed answers must work even if microphone or webcam access fails.
- Privacy: API keys must never be committed; local demo profile must not be presented as production authentication.
- Safety: body/delivery metrics must stay observable and not infer emotion, personality, protected traits, or winner likelihood.
- Maintainability: backend code should be modular and tested; frontend code should be split if the project continues.
- Accessibility: UI text should be readable, navigation clear, and controls labeled.
- Portability: app should run from documented local commands on a fresh clone.

## Out Of Scope For This Course MVP

- Production-grade authentication.
- Official judging or winner prediction.
- Emotion, personality, attractiveness, or protected-trait inference.
- Long-term cloud storage of user sessions.
- Enterprise deployment and role-based access control.
- Replacing human coaches or judges.

## Constraints

- Short course timeline.
- Mixed optional API dependencies.
- Browser permission reliability for microphone and webcam.
- Need to demonstrate value even when live model keys are unavailable.
- Need to document AI-assisted development process as part of the grade.

## Requirements Traceability

| Requirement | Implemented In | Evidence |
|---|---|---|
| Case setup | `case-mirror/app.js` setup screen | Demo flow and README |
| Brief generation | local JS plus `/api/live/prepare` | `docs/FRONTEND_GUIDE.md`, `docs/API_OVERVIEW.md` |
| Judge Q&A | rehearsal route | Demo flow |
| Answer grading | local scoring plus `/api/live/grade-answer` | Backend routes and tests |
| Readiness report | report route plus `/api/live/report` | Demo flow and API docs |
| Teachable Machine evidence | browser model assets and body-event summary | `case-mirror/assets/teachable-image/`, frontend guide |
| Safety boundaries | prompts, route sanitization, tests | backend tests and safety docs |
| Local runnability | frontend/backend commands | README |

## Acceptance Criteria

| Requirement | Acceptance Criteria | Verified By |
|---|---|---|
| Case setup | User can enter case prompt and recommendation; app blocks progression if required fields are missing | Manual demo QA |
| Brief generation | App produces a structured case brief and critique from entered materials | Demo flow |
| Judge Q&A | App generates at least five judge-style questions tied to the case/rubric | Demo flow |
| Typed answer fallback | User can answer without microphone or camera | Manual demo QA |
| Follow-up question | Weak or incomplete answer can trigger a follow-up prompt | Demo flow |
| Readiness report | App summarizes strengths, weak spots, missed criteria, and drills | Demo flow |
| Backend fallback | App remains usable when backend/API keys are unavailable | Testing doc |
| Safety boundary | App avoids emotion, personality, protected-trait, winner, or official judging claims | Security docs and backend tests |
| Local runnability | Fresh clone can run frontend and backend using documented commands | README and testing doc |

## Feature-To-Business-Value Map

| Feature | User Pain Point | Business Value |
|---|---|---|
| Case-specific setup | Generic tools do not understand the case prompt or rubric | More relevant practice |
| Judge-style questions | Teams under-practice pressure Q&A | Better presentation defense |
| Typed answers | Mic/camera can fail during demos or practice | Reliable low-friction workflow |
| Follow-ups | Teams often give incomplete answers | Helps expose weak assumptions |
| Readiness report | Feedback is often scattered or delayed | Concrete next-practice plan |
| Observable delivery signals | Teams want delivery feedback but not pseudoscience | Safer coaching evidence |
