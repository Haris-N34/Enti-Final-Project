import pytest

from app.models.schemas import AnalysisResult
from app.pipelines.analysis_pipeline import _assert_safe_report


def test_safety_rejects_banned_language():
    result = AnalysisResult(job_id="job-1", top_issues=["You looked nervous during the opening."])
    with pytest.raises(ValueError):
        _assert_safe_report(result)


def test_safety_allows_observable_language():
    result = AnalysisResult(job_id="job-1", top_issues=["Average transcript pace is above the recommended range."])
    _assert_safe_report(result)

