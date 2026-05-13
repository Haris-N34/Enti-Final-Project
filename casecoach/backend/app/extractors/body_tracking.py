from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from app.models.schemas import BodyFrameObservation, BodyMetrics, VideoMetadata

MIN_LANDMARK_VISIBILITY = 0.45
GESTURE_MOTION_THRESHOLD = 0.045


def analyze_body_posture(frame_paths: list[Path], video_metadata: VideoMetadata) -> tuple[BodyMetrics, list[BodyFrameObservation]]:
    if not frame_paths:
        return BodyMetrics(warnings=["No sampled frames were available for body posture tracking."]), []

    try:
        import cv2
        import mediapipe as mp
    except ImportError:
        return (
            BodyMetrics(
                provider="unavailable",
                sampled_frame_count=len(frame_paths),
                warnings=[
                    "MediaPipe/OpenCV body tracking is not installed. Install the backend with the optional body extra: pip install -e '.[body]'."
                ],
            ),
            [],
        )

    observations: list[BodyFrameObservation] = []
    previous: dict[str, tuple[float, float] | None] | None = None
    pose_solution = mp.solutions.pose
    with pose_solution.Pose(static_image_mode=True, model_complexity=1, enable_segmentation=False) as pose:
        for index, frame_path in enumerate(frame_paths):
            image = cv2.imread(str(frame_path))
            timestamp = _frame_timestamp(index, video_metadata)
            if image is None:
                observations.append(BodyFrameObservation(timestamp=timestamp, pose_visible=False))
                continue
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb)
            if not result.pose_landmarks:
                observations.append(BodyFrameObservation(timestamp=timestamp, pose_visible=False))
                previous = None
                continue
            observation, previous = _observation_from_landmarks(result.pose_landmarks.landmark, timestamp, previous)
            observations.append(observation)

    return compute_body_metrics(observations, video_metadata.duration_seconds, provider="mediapipe_pose"), observations


def compute_body_metrics(
    observations: list[BodyFrameObservation], duration_seconds: float, provider: str = "mediapipe_pose"
) -> BodyMetrics:
    if not observations:
        return BodyMetrics(provider=provider, warnings=["No body tracking observations were generated."])

    visible = [item for item in observations if item.pose_visible]
    visible_count = len(visible)
    frame_count = len(observations)
    if not visible:
        return BodyMetrics(
            provider=provider,
            sampled_frame_count=frame_count,
            analyzed_frame_count=0,
            pose_visible_pct=0.0,
            warnings=["No presenter body pose was detected in sampled frames."],
        )

    center_motion = _clean_numbers(item.shoulder_center_motion for item in visible)
    wrist_motion = _clean_numbers(item.wrist_motion for item in visible)
    minutes = max(duration_seconds / 60.0, frame_count / 60.0, 1 / 60.0)
    gesture_events = sum(1 for value in wrist_motion if value > GESTURE_MOTION_THRESHOLD)
    hands_values = [item.hands_visible for item in visible if item.hands_visible is not None]
    warnings = _metric_warnings(visible_count, frame_count)
    return BodyMetrics(
        provider=provider,
        sampled_frame_count=frame_count,
        analyzed_frame_count=visible_count,
        pose_visible_pct=_round(visible_count / frame_count * 100),
        posture_stability=_round(max(0.0, min(1.0, 1.0 - _avg(center_motion) * 9.0))),
        avg_shoulder_tilt_deg=_round(_avg(_clean_numbers(item.shoulder_tilt_deg for item in visible))),
        avg_torso_lean_deg=_round(_avg(_clean_numbers(item.torso_lean_deg for item in visible))),
        gesture_rate_per_min=_round(gesture_events / minutes),
        hands_visible_pct=_round(sum(1 for value in hands_values if value) / len(hands_values) * 100) if hands_values else None,
        motion_level=_round(_avg(center_motion + wrist_motion)),
        warnings=warnings,
    )


def _observation_from_landmarks(
    landmarks: list[Any], timestamp: float, previous: dict[str, tuple[float, float] | None] | None
) -> tuple[BodyFrameObservation, dict[str, tuple[float, float] | None]]:
    left_shoulder = _point(landmarks, 11)
    right_shoulder = _point(landmarks, 12)
    left_wrist = _point(landmarks, 15)
    right_wrist = _point(landmarks, 16)
    left_hip = _point(landmarks, 23)
    right_hip = _point(landmarks, 24)
    required = [left_shoulder, right_shoulder, left_hip, right_hip]
    confidence = _avg([point[2] for point in required if point is not None])
    pose_visible = len([point for point in required if point and point[2] >= MIN_LANDMARK_VISIBILITY]) >= 4
    if not pose_visible:
        return BodyFrameObservation(timestamp=timestamp, pose_visible=False, landmark_confidence=_round(confidence)), {}

    shoulder_center = _midpoint(left_shoulder, right_shoulder)
    hip_center = _midpoint(left_hip, right_hip)
    shoulder_angle = math.degrees(math.atan2((right_shoulder[1] - left_shoulder[1]), (right_shoulder[0] - left_shoulder[0])))
    shoulder_tilt = min(abs(shoulder_angle), abs(180.0 - abs(shoulder_angle)))
    torso_lean = abs(math.degrees(math.atan2((shoulder_center[0] - hip_center[0]), max(abs(hip_center[1] - shoulder_center[1]), 0.001))))
    center_motion = _distance(shoulder_center, previous.get("shoulder_center") if previous else None)
    wrist_motion = _distance(left_wrist, previous.get("left_wrist") if previous else None) + _distance(
        right_wrist, previous.get("right_wrist") if previous else None
    )
    hands_visible = bool(
        left_wrist
        and right_wrist
        and left_wrist[2] >= MIN_LANDMARK_VISIBILITY
        and right_wrist[2] >= MIN_LANDMARK_VISIBILITY
    )
    next_previous = {
        "shoulder_center": (shoulder_center[0], shoulder_center[1]),
        "left_wrist": (left_wrist[0], left_wrist[1]) if left_wrist else None,
        "right_wrist": (right_wrist[0], right_wrist[1]) if right_wrist else None,
    }
    return (
        BodyFrameObservation(
            timestamp=timestamp,
            pose_visible=True,
            shoulder_tilt_deg=_round(shoulder_tilt),
            torso_lean_deg=_round(torso_lean),
            shoulder_center_motion=_round(center_motion),
            wrist_motion=_round(wrist_motion),
            hands_visible=hands_visible,
            landmark_confidence=_round(confidence),
        ),
        next_previous,
    )


def _point(landmarks: list[Any], index: int) -> tuple[float, float, float] | None:
    if index >= len(landmarks):
        return None
    landmark = landmarks[index]
    return float(landmark.x), float(landmark.y), float(getattr(landmark, "visibility", 1.0) or 0.0)


def _midpoint(a: tuple[float, float, float] | None, b: tuple[float, float, float] | None) -> tuple[float, float]:
    if not a or not b:
        return 0.0, 0.0
    return (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0


def _distance(a: tuple[float, float] | tuple[float, float, float] | None, b: tuple[float, float] | None) -> float:
    if not a or not b:
        return 0.0
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def _frame_timestamp(index: int, video_metadata: VideoMetadata) -> float:
    if video_metadata.duration_seconds > 0:
        return _round(min(float(index), video_metadata.duration_seconds))
    return float(index)


def _metric_warnings(visible_count: int, frame_count: int) -> list[str]:
    visible_pct = visible_count / max(frame_count, 1) * 100
    if visible_pct < 35:
        return ["Presenter pose was visible in fewer than 35% of sampled frames; body metrics may be incomplete."]
    return []


def _clean_numbers(values) -> list[float]:
    return [float(value) for value in values if value is not None and math.isfinite(float(value))]


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _round(value: float) -> float:
    return round(float(value), 2)
