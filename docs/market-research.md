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

## Customer Discovery To Add Before Submission

This section should be completed with real conversations before final submission.

| Source | Person / Role | Date | Evidence Collected | Product Implication |
|---|---|---|---|---|
| Interview | TODO - case competitor | TODO | TODO | TODO |
| Interview | TODO - case coach or TA | TODO | TODO | TODO |
| Peer test | TODO - student team | TODO | TODO | TODO |

Recommended interview questions:

- How do you currently practice for case competition Q&A?
- What feedback do you usually get too late?
- What makes judge questions difficult?
- What would make a rehearsal tool worth using?
- Which output would be most useful: questions, scores, transcript, body/delivery feedback, or final report?
- What would make you distrust an AI-generated coaching report?

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

Case Mirror is worth building if the team can show that case teams need structured, repeated, judge-style rehearsal and that the app produces feedback that is more actionable than generic AI chat. The final submission should strengthen this conclusion with at least two real user or stakeholder conversations.
