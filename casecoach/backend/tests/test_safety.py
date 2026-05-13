import pytest

from app.api.routes_live import LiveGradeResponse, _assert_live_safety
from app.models.schemas import AnalysisResult
from app.pipelines.analysis_pipeline import _assert_safe_report


def test_safety_rejects_banned_language():
    result = AnalysisResult(job_id="job-1", top_issues=["You looked nervous during the opening."])
    with pytest.raises(ValueError):
        _assert_safe_report(result)


def test_safety_allows_observable_language():
    result = AnalysisResult(job_id="job-1", top_issues=["Average transcript pace is above the recommended range."])
    _assert_safe_report(result)


def test_live_safety_rejects_confidence_claims():
    result = LiveGradeResponse(
        content_score=80,
        clarity_score=80,
        evidence_score=80,
        delivery_score=80,
        metrics={},
        feedback=["You projected more confidence during this answer."],
        follow_up_question="What evidence supports that metric?",
    )
    with pytest.raises(ValueError):
        _assert_live_safety(result)
