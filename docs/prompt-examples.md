# Prompt Examples

This file documents AI-assisted development prompts that should be shown in the final evidence package. The text examples below are useful, but screenshots from the actual tools should be added when available.

## Prompt 1: Requirements Engineering

```text
We are building an ENTI 633 AI-assisted software project for student case competition teams. Turn this product idea into user stories, must-have features, nice-to-have features, risks, and out-of-scope items. Keep the scope realistic for a short course project.
```

Human revision:

- Narrowed the product to case rehearsal instead of a generic presentation coach.
- Added typed-answer fallback because microphone access is unreliable in demos.
- Added safety boundaries around body and gesture metrics.

## Prompt 2: Judge-Style Q&A

```text
Given a case prompt, rubric, team recommendation, and slide outline, generate five judge-style questions that pressure-test assumptions, financial logic, implementation risk, market evidence, and rubric fit. Include one adaptive follow-up rule for weak answers.
```

Human revision:

- Changed generic questions into case-competition language.
- Required answer-first, evidence-second feedback.
- Added rubric links so questions were not random.

## Prompt 3: Safety Boundaries

```text
Review this presentation coaching feature for unsafe or overclaimed body-language interpretation. Rewrite the output rules so it only uses observable metrics and does not infer emotion, personality, protected traits, or winner likelihood.
```

Human revision:

- Replaced "confidence" and "nervousness" phrasing with visible coaching proxies.
- Added safety wording to UI and backend documentation.
- Added tests for restricted language.

## Prompt 4: Repository Audit

```text
Audit this repository against ENTI 633 final project requirements. Be strict. Score business problem clarity, market research, AI-assisted development evidence, README quality, documentation, runnability, feature completeness, security, testing, presentation readiness, blog readiness, and submission readiness.
```

Human revision:

- Converted the audit into concrete documentation fixes.
- Added clearly marked slots where real evidence must be supplied by the team.
- Avoided inventing interviews, links, or team names.

## Screenshot Checklist

Add screenshots for:

- AI coding environment generating or revising code.
- AI prompt for requirements/user stories.
- AI prompt for debugging or testing.
- AI prompt for documentation or audit.
- Teachable Machine training/export screen.

Do not include screenshots of raw code in the blog post unless the instructor explicitly permits it. Prefer prompt and app UI screenshots.

## Pending Screenshot Evidence

The screenshot filenames below are evidence slots to fill when the team adds the actual image files under `docs/images/`. Do not cite them as included evidence until the files exist in the repository.

| Prompt Area | Planned Screenshot File | What It Should Show |
|---|---|---|
| Requirements engineering | `docs/images/prompt-requirements.png` | AI helped turn the business idea into requirements and user stories |
| Specialized coding environment | `docs/images/ai-coding-session-1.png` | AI coding tool reviewed and edited repository files |
| Debugging / testing | `docs/images/prompt-debugging.png` | AI helped inspect errors or improve QA checks |
| Documentation audit | `docs/images/prompt-repo-audit.png` | AI helped audit the repo against ENTI 633 requirements |
| Teachable Machine | `docs/images/teachable-machine-training.png` | Browser-side model classes, training, or export evidence |
