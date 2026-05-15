# Market Research

## Research Question

How might student case-competition teams get faster, more realistic practice feedback before they present to judges?

## Target Segment

Primary target users are university students preparing for case competitions, pitch competitions, consulting club events, or case-based course presentations. These teams often need to practice under time pressure, defend assumptions, and improve both content and delivery before receiving formal feedback.

Secondary users include coaches, teaching assistants, instructors, and club executives who want teams to arrive at coaching sessions better prepared.

## Problem Evidence

Observed and expected pain points:

- Teams often practice slides but not judge-style follow-up questions.
- Feedback is usually delayed until a coach, peer, or instructor is available.
- Generic AI chat prompts can produce questions, but they do not preserve a structured rehearsal workflow.
- Presentation tools may help with delivery but do not understand the case rubric or business recommendation.
- Teams need a low-friction way to identify weak assumptions, missing evidence, and unclear answers before the real presentation.

## Customer Discovery Evidence

This table is ready for real validation evidence. It should be filled only with true conversations, tests, dates, and findings.

| Source | Person / Role | Date | Evidence Collected | Product Implication |
|---|---|---|---|---|
| Interview | Student case competitor | Evidence needed | Evidence needed | Evidence needed |
| Interview | Case coach, TA, or experienced competitor | Evidence needed | Evidence needed | Evidence needed |
| Peer test | Student peer tester or team | Evidence needed | Evidence needed | Evidence needed |
| Stakeholder conversation | Club executive, course TA, organizer, or sponsor-side representative | Evidence needed | Evidence needed | Evidence needed |

Recommended interview questions:

- How do you currently practice for case competition Q&A?
- What feedback do you usually get too late?
- What makes judge questions difficult?
- What would make a rehearsal tool worth using?
- Which output would be most useful: questions, scores, transcript, body/delivery feedback, or final report?
- What would make you distrust an AI-generated coaching report?

## Customer Discovery Themes To Validate

### Theme 1: Teams practice slides more than judge defense

The app is designed around the assumption that teams often rehearse the presentation itself but spend less time answering skeptical follow-up questions. Real customer discovery should confirm, revise, or reject this assumption.

### Theme 2: Feedback arrives too late

The app assumes students often depend on coach, peer, or instructor availability. Real discovery should confirm whether a self-serve rehearsal loop would create value before human feedback sessions.

### Theme 3: Generic AI chat is useful but unstructured

The app assumes generic chat tools can generate questions but do not preserve a full case workflow from setup to report. Real discovery should test whether users prefer this guided workflow.

### Theme 4: Trust requires transparency

The app assumes users will distrust vague confidence scores or body-language claims. This supports the safety boundary: observable delivery signals only, not emotion, personality, or winner prediction.

## Validation Matrix

| Pain Point Found | Evidence Source | App Feature That Responds | Status |
|---|---|---|---|
| Teams under-practice judge Q&A | Customer discovery evidence needed | Judge-style question generator | Implemented |
| Teams struggle to defend assumptions | Customer discovery evidence needed | Follow-up questions and critique | Implemented |
| Feedback is delayed | Customer discovery evidence needed | Self-serve typed rehearsal | Implemented |
| Generic AI chat lacks structure | Competitive analysis and interviews to validate | Setup -> brief -> Q&A -> report workflow | Implemented |
| AI feedback can be distrusted | Safety review and interviews to validate | Observable evidence, warnings, no winner prediction | Implemented |

## Market Opportunity

Case Mirror has a focused opportunity because it targets a specific recurring workflow in business education: preparing teams for high-pressure case presentations. The product is intentionally narrower than a generic presentation coach or chatbot. That focus creates a clearer value proposition:

- Case-specific setup instead of generic speaking practice.
- Rubric-aware critique instead of broad presentation tips.
- Judge-style Q&A instead of one-way slide feedback.
- Evidence-based report instead of vague encouragement.
- Demo-safe typed fallback so teams can use it even when audio/camera permissions fail.

## Assumptions

- Students are willing to paste case prompts and slide notes into a practice tool when privacy is explained.
- Teams value realistic follow-up questions more than generic confidence scoring.
- Coaches would prefer students to arrive with a preliminary readiness report.
- A local/static frontend is acceptable for an MVP if the workflow is easy to demo.

## Risks

- Students may not trust AI feedback without transparent evidence.
- Case materials may be confidential; privacy language must be clear.
- Body/gesture metrics can be misread as personality or emotion analysis, so safety framing is required.
- If backend model keys are missing, the app must still demonstrate a reliable local fallback.

## Research Conclusion

Case Mirror is worth building if the team can show that case teams need structured, repeated, judge-style rehearsal and that the app produces feedback that is more actionable than generic AI chat. The final submission should strengthen this conclusion with real user or stakeholder conversations recorded in [customer-discovery-notes.md](./customer-discovery-notes.md).
