from __future__ import annotations

from app.models.rubric import parse_rubric
from app.models.schemas import RubricScore, Transcript


def score_content(transcript: Transcript, rubric_text: str) -> dict[str, RubricScore]:
    joined = " ".join(segment.text for segment in transcript.segments).lower()
    rubric = parse_rubric(rubric_text)
    scores: dict[str, RubricScore] = {}
    for dimension, weight in rubric:
        score = 60.0
        evidence: list[dict[str, object]] = []
        issues: list[str] = []
        fixes: list[str] = []
        keywords = [token.lower().strip("/,()") for token in dimension.split() if len(token) > 4]
        if any(keyword in joined for keyword in keywords):
            score += 10
            evidence.append({"summary": f"Transcript references language related to {dimension}."})
        else:
            issues.append(f"{dimension} is not clearly evidenced in the transcript.")
            fixes.append(f"Add one explicit sentence or slide note that addresses {dimension}.")
        if any(term in joined for term in ("recommend", "because", "metric", "risk", "implementation")):
            score += 5
        scores[dimension] = RubricScore(
            dimension=dimension,
            weight=weight,
            score=max(35.0, min(90.0, score)),
            evidence=evidence,
            issues=issues,
            fixes=fixes,
        )
    return scores

