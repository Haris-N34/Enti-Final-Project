from __future__ import annotations

from app.models.schemas import SpeakerStats, Transcript


def compute_speaker_stats(transcript: Transcript) -> list[SpeakerStats]:
    totals: dict[str, list[float]] = {}
    for segment in transcript.segments:
        totals.setdefault(segment.speaker, []).append(max(0.0, segment.end - segment.start))
    total_time = sum(sum(values) for values in totals.values())
    output: list[SpeakerStats] = []
    for speaker, turns in sorted(totals.items()):
        speaking_time = sum(turns)
        output.append(
            SpeakerStats(
                speaker=speaker,
                speaking_time_sec=round(speaking_time, 2),
                speaking_share=round(speaking_time / total_time, 4) if total_time else 0.0,
                avg_turn_length_sec=round(speaking_time / len(turns), 2) if turns else 0.0,
            )
        )
    return output

