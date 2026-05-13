from app.extractors.body_tracking import compute_body_metrics
from app.models.schemas import BodyFrameObservation


def test_body_metrics_summarize_visible_pose_and_gestures():
    observations = [
        BodyFrameObservation(timestamp=0, pose_visible=True, shoulder_tilt_deg=2, torso_lean_deg=4, shoulder_center_motion=0.01, wrist_motion=0.01, hands_visible=True),
        BodyFrameObservation(timestamp=1, pose_visible=True, shoulder_tilt_deg=4, torso_lean_deg=6, shoulder_center_motion=0.02, wrist_motion=0.08, hands_visible=True),
        BodyFrameObservation(timestamp=2, pose_visible=False),
        BodyFrameObservation(timestamp=3, pose_visible=True, shoulder_tilt_deg=3, torso_lean_deg=5, shoulder_center_motion=0.01, wrist_motion=0.07, hands_visible=False),
    ]

    metrics = compute_body_metrics(observations, duration_seconds=60)

    assert metrics.provider == "mediapipe_pose"
    assert metrics.sampled_frame_count == 4
    assert metrics.analyzed_frame_count == 3
    assert metrics.pose_visible_pct == 75
    assert metrics.avg_shoulder_tilt_deg == 3
    assert metrics.avg_torso_lean_deg == 5
    assert metrics.gesture_rate_per_min == 2
    assert metrics.hands_visible_pct == 66.67
    assert metrics.posture_stability > 0.8


def test_body_metrics_warn_when_pose_visibility_is_low():
    observations = [
        BodyFrameObservation(timestamp=0, pose_visible=False),
        BodyFrameObservation(timestamp=1, pose_visible=False),
        BodyFrameObservation(timestamp=2, pose_visible=True, shoulder_tilt_deg=2, torso_lean_deg=4, shoulder_center_motion=0.01, wrist_motion=0.01),
    ]

    metrics = compute_body_metrics(observations, duration_seconds=3)

    assert metrics.pose_visible_pct == 33.33
    assert metrics.warnings
