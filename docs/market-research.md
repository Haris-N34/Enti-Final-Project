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

The final presentation deck records two direct validation signals from student competition contexts. These notes should be treated as summarized customer-discovery evidence from the presentation materials, not as full interview transcripts.

| Source | Person / Role | Date | Evidence Collected | Product Implication |
|---|---|---|---|---|
| Interview | ENACTUS participant or stakeholder | May 2026, exact date not specified in deck | The deck states that ENACTUS feedback supported the need for competition-specific pitch preparation. The included quote was: “I think Enactus is a perfect paradigm for an idea like this, since our pitching style is more storytelling-skewed.” | Confirms that Case Mirror should focus on pitch/storytelling defense and judge-style preparation, not just generic case knowledge. |
| Interview | JDC participant or stakeholder | May 2026, exact date not specified in deck | The deck states that interviews with ENACTUS and JDC confirmed the gap is not general knowledge, but competition-specific pitch prep. | Supports the product’s focus on panel-style Q&A, rubric alignment, delivery feedback, and a case-specific readiness report. |
| Competitive analysis | Alternative-tool review from final deck | May 2026 | The deck compares ChatGPT/Gemini/Claude, CaseCoach, Soreno AI, PrepLounge, Yoodli/Orai, and YouTube/Coursera. Each alternative addresses only part of the problem, such as brainstorming, interview prep, speech feedback, or passive learning. | Strengthens the market gap: Case Mirror combines strategy critique, delivery feedback, and judge simulation in one guided workflow. |
| Demo validation | Final presentation demo and QA evidence | May 2026 | The deck includes a demo-video slide, and repository QA confirms the local app completed setup → brief → Q&A → report. | Supports that the MVP is not only conceptual; it has a working demonstration path. |

## Validated Discovery Themes

### Theme 1: Teams need competition-specific pitch preparation

The ENACTUS/JDC validation summarized in the final deck supports the idea that the gap is not simply “students need more business knowledge.” The more specific problem is that teams need to rehearse the way they will defend their story, assumptions, recommendation, implementation plan, and tradeoffs in a live competition setting.

### Theme 2: Existing tools are fragmented

The competitive analysis shows that current options are split across generic AI brainstorming, interview preparation, speech coaching, passive learning, and peer practice. Case Mirror’s differentiation is the structured workflow from case setup to brief, Q&A, and final readiness report.

### Theme 3: Delivery feedback must be honest and limited

The deck and repository both emphasize ethical framing. Case Mirror should not claim to detect emotion, personality, confidence, or winner likelihood. Delivery feedback should stay limited to observable coaching signals and practice suggestions.

### Theme 4: The MVP should prioritize demo reliability

The repository QA confirms that typed-answer rehearsal is the safest demo path. Microphone, webcam, Teachable Machine, and provider-backed AI features should be treated as progressive enhancements, not demo-critical dependencies.

## Validation Matrix

| Pain Point Found | Evidence Source | App Feature That Responds | Status |
|---|---|---|---|
| Teams lack a structured competition-prep workflow | Final deck, slide 2 pain points | Setup → brief → Q&A → report workflow | Implemented |
| Teams need competition-specific pitch prep, not generic knowledge | ENACTUS/JDC validation summarized in final deck | Case-specific prompt/rubric/recommendation setup | Implemented |
| Teams need realistic judging simulation | Final deck, slide 2 and slide 4 | Panel-style judge questions and adaptive follow-ups | Implemented |
| Students need actionable feedback before competition day | Final deck, slide 6 feature/pain-point map | Per-answer feedback and final readiness report | Implemented |
| Existing tools solve only part of the workflow | Final deck, slide 3 competitive analysis | Strategy critique + communication feedback + judge simulation | Implemented in MVP form |
| AI coaching can overclaim body-language meaning | Final deck, slide 6; repo safety docs | Ethical framing; no emotion/personality analysis | Implemented |
| Demo reliability matters | Repository QA evidence | Typed-answer fallback and local/static demo path | Implemented |

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

Case Mirror is worth building because the validated problem is specific: student competition teams need a structured way to rehearse competition-specific pitch defense, not just another generic presentation coach or chatbot. The final deck’s ENACTUS/JDC validation and competitive analysis support the market gap, while the repository QA shows a working MVP path. The strongest current evidence is sufficient for a course MVP, but future product development should collect fuller interview notes, more peer-demo tests, and direct coach/organizer feedback before claiming broader market traction.
