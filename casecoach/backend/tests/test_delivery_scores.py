from app.models.schemas import Transcript, TranscriptSegment
from app.scoring.delivery_scores import compute_delivery_metrics, count_fillers, word_count


def test_word_and_filler_counts_are_stable():
    text = "Um, we recommend this because, you know, the metric is clear."
    assert word_count(text) == 11
    assert count_fillers(text) == 2


def test_delivery_metrics_include_wpm_and_pauses():
    transcript = Transcript(
        segments=[
            TranscriptSegment(start=0, end=10, text="We recommend a pilot because it reduces risk."),
            TranscriptSegment(start=13, end=20, text="The metric is contribution margin."),
        ]
    )
    metrics = compute_delivery_metrics(transcript)
    assert metrics.word_count == 13
    assert metrics.long_pause_count == 1
    assert metrics.long_pauses[0]["duration"] == 3

