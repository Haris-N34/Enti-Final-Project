import json

from app.api.routes_live import (
    LiveReportRequest,
    _fallback_report,
    _assert_report_safety,
    _normalize_evidence_bundle,
    _persist_live_evidence,
)


def _payload() -> LiveReportRequest:
    return LiveReportRequest(
        session_id="session-1",
        company_name="EcoRide",
        case_prompt="Should EcoRide expand with a partnership pilot?",
        judging_criteria="Financial feasibility\nRisk mitigation",
        team_recommendation="Launch a university transit partnership pilot.",
        slide_outline="1. Recommendation\n2. Metrics\n3. Risks",
        answers=[
            {
                "questionNumber": 1,
                "questionText": "What proves success?",
                "answerText": "A 65 percent utilization rate in 90 days proves the pilot is working.",
                "followUp": {"followUpText": "Why 65 percent?"},
                "followUpAnswer": "That threshold keeps battery servicing inside the margin target.",
                "metrics": {
                    "wordCount": 13,
                    "fillerWordCount": 0,
                    "approximateWordsPerMinute": 120,
                    "body": {
                        "poseVisiblePct": 88,
                        "faceVisiblePct": 91,
                        "cameraFacingPct": 58,
                        "postureAlignmentScore": 76,
                        "postureStabilityScore": 82,
                        "postureStability": 79,
                        "gestureRatePerMin": 8,
                        "handsVisiblePct": 42,
                        "movementControlScore": 67,
                        "bodyPositioningScore": 69,
                        "hiddenHandsPct": 48,
                        "teachableDominantClass": "Hands too low / hidden",
                        "teachableGoodPct": 38,
                        "teachableCautionPct": 34,
                        "teachableBadPct": 28,
                        "teachableBehaviorScore": 62,
                    },
                },
            }
        ],
        body_events=[
            {
                "timestamp": "2026-05-14T00:00:00Z",
                "questionNumber": 1,
                "poseVisible": True,
                "faceVisible": True,
                "cameraFacingScore": 58,
                "postureAlignmentScore": 76,
                "handsVisibleScore": 42,
                "movementControlScore": 67,
                "bodyPositioningScore": 69,
                "teachableDominantClass": "Hands too low / hidden",
            }
        ],
        local_report={},
    )


def test_live_evidence_bundle_preserves_answers_metrics_and_events():
    evidence = _normalize_evidence_bundle(_payload())

    assert evidence["schema_version"] == "live_evidence_v2"
    assert evidence["body_metrics_version"] == "body_metrics_v2"
    assert evidence["session_id"] == "session-1"
    assert evidence["answers"][0]["followUpAnswer"] == "That threshold keeps battery servicing inside the margin target."
    assert evidence["answers"][0]["metrics"]["body"]["teachableDominantClass"] == "Hands too low / hidden"
    assert evidence["body_events"][0]["teachableDominantClass"] == "Hands too low / hidden"
    assert evidence["body_summary"]["dominantClass"] == "Hands too low / hidden"
    assert evidence["gesture_events"][0]["teachableDominantClass"] == "Hands too low / hidden"
    assert evidence["gesture_summary"]["dominantClass"] == "Hands too low / hidden"


def test_live_evidence_persistence_writes_expected_files(tmp_path):
    evidence = _normalize_evidence_bundle(_payload())
    session_dir, warnings = _persist_live_evidence(evidence, tmp_path)

    assert warnings == []
    assert (session_dir / "evidence.json").exists()
    assert (session_dir / "body_events.jsonl").exists()
    assert (session_dir / "gesture_events.jsonl").exists()
    saved = json.loads((session_dir / "evidence.json").read_text(encoding="utf-8"))
    assert saved["session_id"] == "session-1"
    assert "Hands too low / hidden" in (session_dir / "body_events.jsonl").read_text(encoding="utf-8")
    assert "Hands too low / hidden" in (session_dir / "gesture_events.jsonl").read_text(encoding="utf-8")


def test_fallback_report_uses_evidence_specific_details():
    evidence = _normalize_evidence_bundle(_payload())
    report = _fallback_report(evidence)

    assert report["bodyMovement"]["dominantClass"] == "Hands too low / hidden"
    assert report["bodyMovement"]["cameraFacingPct"] == 58
    assert report["bodyMovement"]["handsVisiblePct"] == 42
    assert report["bodyMovement"]["movementControlScore"] == 67
    assert len(report["bodyMovement"]["drills"]) >= 3
    assert any("65 percent" in item["currentEvidence"] for item in report["tangibleImprovements"])
    assert any("Camera-facing estimate" in item["currentEvidence"] for item in report["tangibleImprovements"])
    assert "hands visible" in report["bodyMovement"]["movementDrill"].lower()
    assert report["bestAnswer"]["questionNumber"] == 1


def test_report_safety_rejects_appearance_and_outcome_language():
    for phrase in ["nervous", "personality", "attractive", "winner"]:
        try:
            _assert_report_safety({"weaknesses": [phrase]})
        except ValueError:
            continue
        raise AssertionError(f"Expected safety rejection for {phrase}")
