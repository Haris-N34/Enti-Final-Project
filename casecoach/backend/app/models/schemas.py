from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    uploaded = "uploaded"
    preprocessing = "preprocessing"
    transcribing = "transcribing"
    extracting_slides = "extracting_slides"
    reasoning = "reasoning"
    scoring = "scoring"
    completed = "completed"
    failed = "failed"


class UploadContext(BaseModel):
    case_prompt: str = ""
    rubric: str = ""
    team_members: list[str] = Field(default_factory=list)
    presentation_length_limit_minutes: int | None = None
    qa_included: bool = False
    analysis_mode: Literal["fast", "deep", "delivery_only", "slides_only", "qa_only", "full"] = "fast"


class UploadResponse(BaseModel):
    job_id: str
    status: JobStatus
    warnings: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str


class StatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    error: str | None = None
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    paths: dict[str, str] = Field(default_factory=dict)


class VideoMetadata(BaseModel):
    duration_seconds: float = 0.0
    fps: float = 0.0
    width: int = 0
    height: int = 0
    audio_channels: int = 0
    format_name: str = ""
    likely_format: str = "unknown"


class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float
    confidence: float | None = None


class TranscriptSegment(BaseModel):
    start: float
    end: float
    speaker: str = "SPEAKER_00"
    text: str
    words: list[WordTimestamp] = Field(default_factory=list)


class Transcript(BaseModel):
    segments: list[TranscriptSegment] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SpeakerStats(BaseModel):
    speaker: str
    speaking_time_sec: float
    speaking_share: float
    avg_turn_length_sec: float
    interruptions: int = 0


class SlideResult(BaseModel):
    slide_id: str
    slide_number: int
    image_path: str | None = None
    title: str = ""
    first_seen: float | None = None
    last_seen: float | None = None
    ocr_text: str = ""
    text_density: str = "unknown"
    readability_score: int | None = None
    chart_detected: bool = False
    chart_issues: list[str] = Field(default_factory=list)
    speaker_alignment: str = "unknown"
    speaker_missed_points: list[str] = Field(default_factory=list)
    recommended_fix: str = ""
    warnings: list[str] = Field(default_factory=list)


class DeliveryMetrics(BaseModel):
    word_count: int = 0
    speaking_duration_sec: float = 0.0
    average_wpm: float = 0.0
    filler_words_per_minute: float = 0.0
    filler_word_count: int = 0
    long_pause_count: int = 0
    long_pauses: list[dict[str, float]] = Field(default_factory=list)
    observable_note: str = "Metrics are computed from transcript timing and text."


class TimestampedEvidence(BaseModel):
    start: float
    end: float
    type: str
    severity: Literal["low", "medium", "high"] = "medium"
    speaker: str | None = None
    slide_id: str | None = None
    summary: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    fix: str = ""


class TimelineEvent(BaseModel):
    start: float
    end: float
    speaker: str | None = None
    slide: str | None = None
    transcript: str = ""
    delivery_metrics: dict[str, Any] = Field(default_factory=dict)
    content_tags: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class RubricScore(BaseModel):
    dimension: str
    weight: float
    score: float
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    fixes: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    job_id: str
    video_metadata: VideoMetadata = Field(default_factory=VideoMetadata)
    transcript: Transcript = Field(default_factory=Transcript)
    speakers: list[SpeakerStats] = Field(default_factory=list)
    slides: list[SlideResult] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    delivery_metrics: DeliveryMetrics = Field(default_factory=DeliveryMetrics)
    slide_metrics: dict[str, Any] = Field(default_factory=dict)
    content_scores: dict[str, RubricScore] = Field(default_factory=dict)
    team_scores: dict[str, Any] = Field(default_factory=dict)
    qa_scores: dict[str, Any] = Field(default_factory=dict)
    overall_score: float = 0.0
    top_strengths: list[str] = Field(default_factory=list)
    top_issues: list[str] = Field(default_factory=list)
    recommended_drills: list[str] = Field(default_factory=list)
    timestamped_evidence: list[TimestampedEvidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

