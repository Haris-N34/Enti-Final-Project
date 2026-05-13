from __future__ import annotations

DEFAULT_RUBRIC = [
    ("Problem framing", 0.10),
    ("Business insight / analysis depth", 0.15),
    ("Recommendation clarity", 0.15),
    ("Financial reasoning", 0.15),
    ("Implementation feasibility", 0.10),
    ("Risk analysis and mitigation", 0.10),
    ("Slide quality", 0.10),
    ("Delivery and professionalism", 0.10),
    ("Q&A readiness", 0.05),
]


def parse_rubric(raw: str) -> list[tuple[str, float]]:
    if not raw.strip():
        return DEFAULT_RUBRIC
    lines = [line.strip(" -*\t") for line in raw.splitlines() if line.strip()]
    if not lines:
        return DEFAULT_RUBRIC
    weight = round(1 / len(lines), 4)
    return [(line, weight) for line in lines]

