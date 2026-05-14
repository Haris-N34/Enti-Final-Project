from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.config import get_settings
from app.extractors.groq_client import GroqClient
from app.extractors.tavily_client import TavilyClient
from app.extractors.qwen_vl_client import QwenVLClient
from app.scoring.delivery_scores import count_fillers, word_count

router = APIRouter(prefix="/api/live", tags=["live"])


class LivePrepareRequest(BaseModel):
    company: str = ""
    industry: str = ""
    case_prompt: str = ""
    slide_text: str = ""
    presentation_minutes: int = 10


class LivePrepareResponse(BaseModel):
    slide_summary: list[str] = Field(default_factory=list)
    market_context: list[str] = Field(default_factory=list)
    market_sources: list[dict[str, str]] = Field(default_factory=list)
    likely_judge_questions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class LiveMetrics(BaseModel):
    word_count: int = 0
    filler_word_count: int = 0
    estimated_wpm: float = 0.0
    elapsed_seconds: float = 0.0
    pose_visible_pct: float | None = None
    face_visible_pct: float | None = None
    camera_facing_pct: float | None = None
    posture_stability: float | None = None
    posture_alignment_score: float | None = None
    posture_stability_score: float | None = None
    shoulder_tilt_avg: float | None = None
    gesture_rate_per_min: float | None = None
    motion_level: float | None = None
    camera_engagement_proxy_pct: float | None = None
    hands_visible_pct: float | None = None
    movement_control_score: float | None = None
    body_positioning_score: float | None = None
    hidden_hands_pct: float | None = None
    arms_crossed_pct: float | None = None
    excessive_movement_pct: float | None = None
    pointing_pct: float | None = None
    vision_provider: str | None = None
    teachable_top_class: str | None = None
    teachable_top_confidence_pct: float | None = None
    teachable_predictions: list[dict[str, Any]] = Field(default_factory=list)
    teachable_behavior_score: float | None = None
    teachable_good_pct: float | None = None
    teachable_bad_pct: float | None = None
    teachable_caution_pct: float | None = None
    teachable_dominant_class: str | None = None
    teachable_dominant_meaning: str | None = None
    teachable_category_pcts: dict[str, float] = Field(default_factory=dict)
    audio_energy_avg: float | None = None
    audio_energy_variation: float | None = None
    silence_pct: float | None = None


class LiveGradeRequest(BaseModel):
    question: str
    answer: str
    slide_text: str = ""
    case_prompt: str = ""
    market_context: list[str] = Field(default_factory=list)
    market_sources: list[dict[str, str]] = Field(default_factory=list)
    metrics: LiveMetrics = Field(default_factory=LiveMetrics)
    elapsed_seconds: float = 60


class LiveGradeResponse(BaseModel):
    content_score: int
    clarity_score: int
    evidence_score: int
    delivery_score: int
    metrics: dict[str, Any]
    feedback: list[str]
    follow_up_question: str
    warnings: list[str] = Field(default_factory=list)


class LiveReportRequest(BaseModel):
    session_id: str = ""
    evidence_bundle: dict[str, Any] = Field(default_factory=dict)
    company_name: str = ""
    industry_context: str = ""
    target_presentation_length: str = ""
    case_prompt: str = ""
    judging_criteria: str = ""
    team_recommendation: str = ""
    slide_outline: str = ""
    team_constraints: str = ""
    brief: dict[str, Any] = Field(default_factory=dict)
    critique: dict[str, Any] = Field(default_factory=dict)
    answers: list[dict[str, Any]] = Field(default_factory=list)
    body_events: list[dict[str, Any]] = Field(default_factory=list)
    body_summary: dict[str, Any] = Field(default_factory=dict)
    body_quality_warnings: list[str] = Field(default_factory=list)
    body_metrics_version: str = ""
    gesture_events: list[dict[str, Any]] = Field(default_factory=list)
    gesture_summary: dict[str, Any] = Field(default_factory=dict)
    local_report: dict[str, Any] = Field(default_factory=dict)


class LiveReportResponse(BaseModel):
    report: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)


class DeepgramTokenResponse(BaseModel):
    access_token: str = ""
    expires_in: int = 0
    warnings: list[str] = Field(default_factory=list)


@router.post("/deepgram-token", response_model=DeepgramTokenResponse)
async def create_deepgram_token() -> DeepgramTokenResponse:
    settings = get_settings()
    if not settings.deepgram_api_key:
        return DeepgramTokenResponse(warnings=["DEEPGRAM_API_KEY is not configured; browser speech fallback will be used."])
    try:
        import httpx
    except ImportError:
        return DeepgramTokenResponse(warnings=["httpx is not installed; Deepgram proxy or browser speech fallback will be used."])

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://api.deepgram.com/v1/auth/grant",
                headers={"Authorization": f"Token {settings.deepgram_api_key}"},
                json={"ttl_seconds": 600},
            )
            response.raise_for_status()
        data = response.json()
        return DeepgramTokenResponse(
            access_token=str(data.get("access_token", "")),
            expires_in=int(data.get("expires_in", 0) or 0),
        )
    except httpx.HTTPStatusError as exc:
        return DeepgramTokenResponse(
            warnings=[
                f"Deepgram token request failed with HTTP {exc.response.status_code}; Deepgram proxy or browser speech fallback will be used."
            ]
        )
    except (httpx.RequestError, ValueError, TypeError) as exc:
        return DeepgramTokenResponse(warnings=[f"Deepgram token request failed; Deepgram proxy or browser speech fallback will be used. {exc}"])


@router.websocket("/deepgram-proxy")
async def deepgram_proxy(websocket: WebSocket) -> None:
    await websocket.accept()
    settings = get_settings()
    if not settings.deepgram_api_key:
        await websocket.send_json({"type": "error", "message": "DEEPGRAM_API_KEY is not configured."})
        await websocket.close(code=1008)
        return
    try:
        import websockets
    except ImportError:
        await websocket.send_json({"type": "error", "message": "websockets is not installed."})
        await websocket.close(code=1011)
        return

    uri = (
        "wss://api.deepgram.com/v1/listen"
        "?model=nova-3&smart_format=true&interim_results=true&utterances=true&diarize=true&punctuate=true"
    )
    try:
        async with websockets.connect(
            uri,
            additional_headers={"Authorization": f"Token {settings.deepgram_api_key}"},
            max_size=8 * 1024 * 1024,
        ) as deepgram:
            await _relay_websockets(websocket, deepgram)
    except WebSocketDisconnect:
        return
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "message": f"Deepgram proxy failed: {exc}"})
            await websocket.close(code=1011)
        except RuntimeError:
            return


@router.post("/prepare", response_model=LivePrepareResponse)
async def prepare_live_rehearsal(payload: LivePrepareRequest) -> LivePrepareResponse:
    fallback = _fallback_prepare(payload)
    warnings: list[str] = []
    settings = get_settings()
    search_results, search_warning = await TavilyClient(settings.tavily_api_key).search(_research_query(payload))
    fallback.market_sources = search_results
    if search_warning:
        warnings.append(search_warning)
    client = QwenVLClient(settings.qwen_vl_base_url, settings.qwen_vl_api_key, settings.qwen_vl_model)
    prompt = _prepare_prompt(payload, search_results)
    response, warning = await client.complete_json(prompt)
    if warning:
        fallback.warnings = warnings + [warning] + fallback.warnings
        return fallback
    try:
        if not isinstance(response, dict):
            fallback.warnings = warnings + fallback.warnings
            return fallback
        return LivePrepareResponse(
            slide_summary=_coerce_strings(response.get("slide_summary"), fallback.slide_summary),
            market_context=_coerce_strings(response.get("market_context"), fallback.market_context),
            market_sources=search_results,
            likely_judge_questions=_coerce_strings(response.get("likely_judge_questions"), fallback.likely_judge_questions)[:8],
            warnings=warnings + _coerce_strings(response.get("warnings"), []),
        )
    except Exception as exc:
        fallback.warnings = warnings + fallback.warnings + [f"Model response could not be parsed; used fallback. {exc}"]
        return fallback


@router.post("/grade-answer", response_model=LiveGradeResponse)
async def grade_live_answer(payload: LiveGradeRequest) -> LiveGradeResponse:
    fallback = _fallback_grade(payload)
    settings = get_settings()
    client = QwenVLClient(settings.qwen_vl_base_url, settings.qwen_vl_api_key, settings.qwen_vl_model)
    response, warning = await client.complete_json(_grade_prompt(payload))
    if warning:
        fallback.warnings.append(warning)
        return fallback
    try:
        if not isinstance(response, dict):
            return fallback
        metrics = fallback.metrics
        metrics.update(response.get("metrics") if isinstance(response.get("metrics"), dict) else {})
        result = LiveGradeResponse(
            content_score=_score(response.get("content_score"), fallback.content_score),
            clarity_score=_score(response.get("clarity_score"), fallback.clarity_score),
            evidence_score=_score(response.get("evidence_score"), fallback.evidence_score),
            delivery_score=_score(response.get("delivery_score"), fallback.delivery_score),
            metrics=metrics,
            feedback=_coerce_strings(response.get("feedback"), fallback.feedback),
            follow_up_question=str(response.get("follow_up_question") or fallback.follow_up_question),
            warnings=_coerce_strings(response.get("warnings"), []),
        )
        _assert_live_safety(result)
        return result
    except Exception as exc:
        fallback.warnings.append(f"Model response could not be parsed; used fallback. {exc}")
        return fallback


@router.post("/report", response_model=LiveReportResponse)
async def generate_live_report(payload: LiveReportRequest) -> LiveReportResponse:
    warnings: list[str] = []
    settings = get_settings()
    evidence = _normalize_evidence_bundle(payload)
    session_dir, persist_warnings = _persist_live_evidence(evidence, settings.data_dir)
    warnings.extend(persist_warnings)
    fallback = _fallback_report(evidence, payload.local_report)

    client = GroqClient(settings.groq_base_url, settings.groq_api_key, settings.groq_model)
    response, warning = await client.complete_json(
        prompt=_report_prompt(evidence),
        system_prompt=(
            "You are a strict but helpful university case competition coach. "
            "Return JSON only. Use observable metrics and transcript evidence. "
            "Do not infer emotion, personality, protected traits, confidence, nervousness, or official judging outcomes."
        ),
    )
    if warning:
        warnings.append(warning)
        _write_report_file(session_dir, fallback)
        return LiveReportResponse(report=fallback, warnings=warnings)
    if not isinstance(response, dict):
        warnings.append("Groq response was not a JSON object; used fallback report.")
        _write_report_file(session_dir, fallback)
        return LiveReportResponse(report=fallback, warnings=warnings)

    report = _coerce_report_shape(response, fallback)
    try:
        _assert_report_safety(report)
    except ValueError as exc:
        warnings.append(f"{exc}; used fallback report.")
        _write_report_file(session_dir, fallback)
        return LiveReportResponse(report=fallback, warnings=warnings)
    _write_report_file(session_dir, report)
    return LiveReportResponse(report=report, warnings=warnings)


def _prepare_prompt(payload: LivePrepareRequest, search_results: list[dict[str, str]]) -> str:
    return f"""
Return JSON only.
You are preparing a university case competition live rehearsal.
Read the slide text and case prompt. Produce:
- slide_summary: 4 concise bullets about what the slides appear to argue
- market_context: 4 careful market/industry context bullets based on the supplied search snippets when available. Label assumptions.
- likely_judge_questions: 6 judge-style questions based on slides, market, risks, implementation, and metrics
- warnings: any missing information

Company: {payload.company}
Industry: {payload.industry}
Presentation minutes: {payload.presentation_minutes}
Case prompt:
{payload.case_prompt}

Slide text:
{payload.slide_text[:14000]}

Market search snippets:
{json.dumps(search_results, ensure_ascii=False)[:8000]}
"""


def _grade_prompt(payload: LiveGradeRequest) -> str:
    return f"""
Return JSON only.
Grade this live case competition answer using only the supplied question, answer, case prompt, and slide text.
Use the supplied delivery/body metrics as observable signals. Do not infer emotion, personality, protected traits, honesty, confidence, nervousness, authority, professionalism, leadership potential, official judge decisions, or winner likelihood.
Fields:
content_score: integer 0-100
clarity_score: integer 0-100
evidence_score: integer 0-100
delivery_score: integer 0-100
metrics: object
feedback: 3 short actionable bullets
follow_up_question: one adaptive judge follow-up
warnings: array

Question: {payload.question}
Elapsed seconds: {payload.elapsed_seconds}
Answer:
{payload.answer[:8000]}

Observable delivery and body metrics:
{payload.metrics.model_dump_json()}

Market context:
{json.dumps(payload.market_context, ensure_ascii=False)[:3000]}

Market sources:
{json.dumps(payload.market_sources, ensure_ascii=False)[:3000]}

Case prompt:
{payload.case_prompt[:4000]}

Slide text:
{payload.slide_text[:8000]}
"""


async def _relay_websockets(websocket: WebSocket, deepgram: Any) -> None:
    async def browser_to_deepgram() -> None:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                await deepgram.close()
                return
            if message.get("bytes") is not None:
                await deepgram.send(message["bytes"])
            elif message.get("text"):
                await deepgram.send(message["text"])

    async def deepgram_to_browser() -> None:
        async for message in deepgram:
            if isinstance(message, bytes):
                await websocket.send_bytes(message)
            else:
                await websocket.send_text(message)

    tasks = [
        asyncio.create_task(browser_to_deepgram()),
        asyncio.create_task(deepgram_to_browser()),
    ]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    for task in pending:
        task.cancel()
    for task in done:
        task.result()


def _fallback_prepare(payload: LivePrepareRequest) -> LivePrepareResponse:
    keywords = _keywords(f"{payload.company} {payload.industry} {payload.case_prompt} {payload.slide_text}")
    company = payload.company or "the client"
    return LivePrepareResponse(
        slide_summary=[
            f"The material appears to focus on {', '.join(keywords[:3]) or 'the recommendation and supporting logic'}.",
            "The live score will be stronger if the recommendation, metric, risk, and implementation owner are stated plainly.",
            "Slides should connect each major claim to a judge-relevant criterion.",
        ],
        market_context=[
            f"Assumption to verify: {company}'s target market has enough demand for the proposed recommendation.",
            "Look for current market size, growth, customer pain points, competitor response, and regulatory constraints.",
            "Use only sourced numbers in the final presentation; label unsourced estimates as assumptions.",
        ],
        market_sources=[],
        likely_judge_questions=[
            "What is your recommendation in one sentence?",
            "Which assumption would break your recommendation first?",
            "What metric proves success within the first 30 to 90 days?",
            "Why is this option better than the strongest alternative?",
            "What implementation risk would you mitigate first?",
            "What market evidence supports your target customer choice?",
        ],
        warnings=["Used local fallback preparation. Configure DashScope and internet/search tooling for deeper research."],
    )


def _fallback_grade(payload: LiveGradeRequest) -> LiveGradeResponse:
    words = word_count(payload.answer)
    fillers = count_fillers(payload.answer)
    elapsed = max(payload.metrics.elapsed_seconds or payload.elapsed_seconds, 1)
    wpm = round(words / elapsed * 60, 1)
    has_number = any(char.isdigit() for char in payload.answer)
    has_risk = any(term in payload.answer.lower() for term in ("risk", "tradeoff", "mitigat", "downside"))
    has_because = any(term in payload.answer.lower() for term in ("because", "therefore", "so that", "we recommend"))
    content = min(95, 45 + (20 if words > 35 else 5) + (15 if has_because else 0) + (10 if has_risk else 0))
    clarity = min(95, 70 + (10 if 90 <= wpm <= 175 else -10) - min(fillers * 3, 15))
    evidence = min(95, 50 + (25 if has_number else 0) + (10 if "metric" in payload.answer.lower() else 0))
    delivery = _delivery_score(payload.metrics, wpm, fillers)
    return LiveGradeResponse(
        content_score=max(20, int(content)),
        clarity_score=max(20, int(clarity)),
        evidence_score=max(20, int(evidence)),
        delivery_score=delivery,
        metrics={
            **payload.metrics.model_dump(exclude_none=True),
            "word_count": words,
            "filler_word_count": fillers,
            "elapsed_seconds": elapsed,
            "estimated_wpm": wpm,
        },
        feedback=[
            "Start with the direct answer before adding context.",
            "Name one metric or decision threshold to make the answer defensible.",
            _delivery_feedback(payload.metrics, wpm, fillers),
        ],
        follow_up_question="What specific evidence would make that answer convincing to a skeptical judge?",
        warnings=["Used deterministic fallback grading."],
    )


def _keywords(text: str) -> list[str]:
    stop = {"that", "with", "from", "this", "your", "will", "case", "slide", "market", "business", "recommendation"}
    counts: dict[str, int] = {}
    for token in text.lower().replace("/", " ").replace("-", " ").split():
        cleaned = "".join(char for char in token if char.isalnum())
        if len(cleaned) > 3 and cleaned not in stop:
            counts[cleaned] = counts.get(cleaned, 0) + 1
    return [item for item, _count in sorted(counts.items(), key=lambda pair: pair[1], reverse=True)[:8]]


def _research_query(payload: LivePrepareRequest) -> str:
    terms = " ".join(item for item in [payload.company, payload.industry, payload.case_prompt[:180]] if item.strip())
    return terms or "case competition market analysis industry trends"


def _delivery_score(metrics: LiveMetrics, wpm: float, fillers: int) -> int:
    score = 78
    if wpm > 185 or (0 < wpm < 90):
        score -= 10
    score -= min(fillers * 2, 14)
    if metrics.posture_stability is not None:
        score += int((metrics.posture_stability - (70 if metrics.posture_stability > 1 else 0.7)) * (0.12 if metrics.posture_stability > 1 else 18))
    if metrics.body_positioning_score is not None:
        score += int((metrics.body_positioning_score - 70) * 0.18)
    if metrics.camera_facing_pct is not None and metrics.camera_facing_pct < 45:
        score -= 8
    if metrics.hands_visible_pct is not None and metrics.hands_visible_pct < 45:
        score -= 6
    if metrics.movement_control_score is not None and metrics.movement_control_score < 55:
        score -= 5
    if metrics.camera_engagement_proxy_pct is not None and metrics.camera_engagement_proxy_pct < 45:
        score -= 8
    if metrics.silence_pct is not None and metrics.silence_pct > 45:
        score -= 6
    if metrics.audio_energy_variation is not None and metrics.audio_energy_variation < 0.01:
        score -= 4
    if metrics.teachable_behavior_score is not None:
        score += int((metrics.teachable_behavior_score - 70) * 0.2)
    if metrics.teachable_bad_pct is not None and metrics.teachable_bad_pct > 30:
        score -= int((metrics.teachable_bad_pct - 30) * 0.22)
    if metrics.teachable_good_pct is not None and metrics.teachable_good_pct > 35:
        score += int((metrics.teachable_good_pct - 35) * 0.08)
    if metrics.teachable_category_pcts.get("Pointing", 0.0) > 32:
        score -= int((metrics.teachable_category_pcts["Pointing"] - 32) * 0.2)
    return max(20, min(95, score))


def _delivery_feedback(metrics: LiveMetrics, wpm: float, fillers: int) -> str:
    if wpm > 185:
        return "Slow the pace and pause before key evidence or numbers."
    if fillers >= 4:
        return "Reduce filler words by pausing silently before the next point."
    if metrics.camera_facing_pct is not None and metrics.camera_facing_pct < 45:
        return "Camera-facing estimate was low; practice the first sentence with your face centered toward the camera."
    if metrics.hands_visible_pct is not None and metrics.hands_visible_pct < 45:
        return "Hands were not visible enough; keep them in frame near mid-torso during key claims."
    if metrics.movement_control_score is not None and metrics.movement_control_score < 55:
        return "Movement control was low; reset to a still posture between major claims."
    if metrics.camera_engagement_proxy_pct is not None and metrics.camera_engagement_proxy_pct < 45:
        return "Your camera-facing posture proxy was low; practice the first sentence facing the camera."
    if metrics.silence_pct is not None and metrics.silence_pct > 45:
        return "There was a lot of low-audio time; practice the transition into the answer before restarting."
    if metrics.audio_energy_variation is not None and metrics.audio_energy_variation < 0.01:
        return "Voice energy variation was low; emphasize the recommendation and key metric more clearly."
    if metrics.teachable_behavior_score is not None and metrics.teachable_behavior_score < 55:
        return "Gesture behavior score was low; keep hands visible, avoid crossed arms, and reduce extra motion."
    if metrics.teachable_dominant_class == "Hands too low / hidden":
        return "Hands were hidden often; bring your hands into frame during key points."
    if metrics.teachable_dominant_class == "Arms crossed":
        return "Arms were crossed frequently; use an open posture when giving the recommendation."
    if metrics.teachable_dominant_class == "Excessive movement":
        return "Movement was high; anchor your hands before and after each core claim."
    if metrics.teachable_dominant_class == "Pointing" and metrics.teachable_category_pcts.get("Pointing", 0.0) > 32:
        return "Pointing was overused; switch to open palms or neutral hands between emphasis moments."
    if metrics.teachable_good_pct is not None and metrics.teachable_good_pct >= 45:
        return "Gesture mix looked strong overall; keep the same open/neutral hand balance while tightening evidence."
    return "Delivery metrics are usable; focus on tighter evidence and risk handling."


def _normalize_evidence_bundle(payload: LiveReportRequest) -> dict[str, Any]:
    source = payload.evidence_bundle if isinstance(payload.evidence_bundle, dict) else {}
    session_id = str(source.get("session_id") or payload.session_id or "").strip()
    now = datetime.now(timezone.utc).isoformat()
    session = source.get("session") if isinstance(source.get("session"), dict) else {}
    case_inputs = source.get("case_inputs") if isinstance(source.get("case_inputs"), dict) else {}
    prep = source.get("prep") if isinstance(source.get("prep"), dict) else {}
    answers = _coerce_dict_list(source.get("answers") or payload.answers)
    body_events = _coerce_dict_list(source.get("body_events") or payload.body_events or source.get("gesture_events") or payload.gesture_events)
    gesture_events = _coerce_dict_list(source.get("gesture_events") or payload.gesture_events or body_events)
    body_summary = source.get("body_summary") if isinstance(source.get("body_summary"), dict) else payload.body_summary
    gesture_summary = source.get("gesture_summary") if isinstance(source.get("gesture_summary"), dict) else payload.gesture_summary
    body_quality_warnings = source.get("body_quality_warnings") if isinstance(source.get("body_quality_warnings"), list) else payload.body_quality_warnings
    evidence = {
        "schema_version": "live_evidence_v2",
        "body_metrics_version": str(source.get("body_metrics_version") or payload.body_metrics_version or "body_metrics_v2"),
        "created_at": str(source.get("created_at") or now),
        "session_id": session_id or _safe_session_id(payload.company_name or "session"),
        "session": {
            "id": session_id or payload.session_id,
            "created_at": session.get("created_at", ""),
            "generated_at": now,
            "company_name": session.get("company_name") or payload.company_name,
            "industry_context": session.get("industry_context") or payload.industry_context,
            "target_presentation_length": session.get("target_presentation_length") or payload.target_presentation_length,
        },
        "case_inputs": {
            "case_prompt": case_inputs.get("case_prompt") or payload.case_prompt,
            "judging_criteria": case_inputs.get("judging_criteria") or payload.judging_criteria,
            "team_recommendation": case_inputs.get("team_recommendation") or payload.team_recommendation,
            "team_constraints": case_inputs.get("team_constraints") or payload.team_constraints,
            "slide_outline": case_inputs.get("slide_outline") or payload.slide_outline,
        },
        "prep": {
            "brief": prep.get("brief") if isinstance(prep.get("brief"), dict) else payload.brief,
            "critique": prep.get("critique") if isinstance(prep.get("critique"), dict) else payload.critique,
            "market_context": prep.get("market_context") if isinstance(prep.get("market_context"), list) else payload.brief.get("marketContext", []),
            "market_sources": prep.get("market_sources") if isinstance(prep.get("market_sources"), list) else payload.brief.get("marketSources", []),
        },
        "answers": answers[:5],
        "body_summary": body_summary if isinstance(body_summary, dict) else {},
        "body_events": body_events[-2500:],
        "body_quality_warnings": [str(item) for item in body_quality_warnings if str(item).strip()],
        "gesture_summary": gesture_summary if isinstance(gesture_summary, dict) else {},
        "gesture_events": gesture_events[-2500:],
        "local_report": payload.local_report if isinstance(payload.local_report, dict) else {},
    }
    if not evidence["body_summary"]:
        evidence["body_summary"] = _summarize_body_events(evidence["body_events"], evidence["answers"])
    if not evidence["gesture_summary"]:
        evidence["gesture_summary"] = evidence["body_summary"] or _summarize_gesture_events(evidence["gesture_events"], evidence["answers"])
    if not evidence["body_quality_warnings"]:
        evidence["body_quality_warnings"] = _report_warnings_from_evidence(evidence, _body_metrics_from_evidence(evidence))
    return evidence


def _report_prompt(evidence: dict[str, Any]) -> str:
    body_events = _coerce_dict_list(evidence.get("body_events") or evidence.get("gesture_events"))[-1500:]
    answers = _coerce_dict_list(evidence.get("answers"))[:5]
    case_inputs = evidence.get("case_inputs", {})
    session = evidence.get("session", {})
    prep = evidence.get("prep", {})
    return f"""
Return JSON only with this exact top-level shape:
{{
  "generatedAt": "ISO timestamp",
  "scores": {{
    "overallReadinessScore": 0-100 int,
    "recommendationStrengthScore": 0-100 int,
    "qnaReadinessScore": 0-100 int,
    "presentationClarityScore": 0-100 int
  }},
  "strengths": ["..."],
  "weaknesses": ["..."],
  "missedCriteria": ["..."],
  "weakAssumptions": ["..."],
  "likelyJudgeConcerns": ["..."],
  "missingMetricsOrEvidence": ["..."],
  "bestAnswer": {{"questionNumber": int, "summary": "...", "score": int}},
  "weakestAnswer": {{"questionNumber": int, "summary": "...", "score": int}},
  "improvedAnswers": [{{"question": "...", "suggestion": "..."}}],
  "nextPracticePlan": ["..."],
  "bodyMovement": {{
    "summary": "...",
    "dominantClass": "...",
    "cameraFacingPct": 0-100 number|null,
    "faceVisiblePct": 0-100 number|null,
    "postureScore": 0-100 number|null,
    "handsVisiblePct": 0-100 number|null,
    "movementControlScore": 0-100 number|null,
    "bodyPositioningScore": 0-100 number|null,
    "goodPct": 0-100 number|null,
    "cautionPct": 0-100 number|null,
    "badPct": 0-100 number|null,
    "topRepeatedIssue": "...",
    "movementDrill": "...",
    "drills": ["camera-facing drill", "posture/framing drill", "hands/movement drill"]
  }},
  "tangibleImprovements": [
    {{"area": "content|delivery|slides", "currentEvidence": "...", "change": "...", "practiceDrill": "..."}}
  ],
  "deliveryMetrics": {{
    "totalFillerWords": int,
    "averageWordsPerMinute": int,
    "bodyMetrics": object|null,
    "note": "..."
  }},
  "reportWarnings": ["..."]
}}

Constraints:
- Ground report in supplied transcript answers and saved body observations only.
- Include at least 3 tangibleImprovements. Each must name what to change and how to practice it.
- Include at least 3 content improvements tied to answer text, and at least 3 delivery/body improvements tied to camera-facing estimate, posture score, hands-visible percentage, movement-control score, or Teachable classes.
- If slide outline exists, include at least one slide/deck improvement.
- Do not infer emotion, personality, confidence, protected traits, winner likelihood, nervousness, authority, professionalism, or official judge decisions.
- Do not mention gesture rate or gestures per minute.
- Keep language practical and actionable for rehearsal.

Company: {session.get("company_name", "")}
Industry context: {session.get("industry_context", "")}
Case prompt: {str(case_inputs.get("case_prompt", ""))[:4000]}
Judging criteria: {str(case_inputs.get("judging_criteria", ""))[:4000]}
Team recommendation: {str(case_inputs.get("team_recommendation", ""))[:4000]}
Slide outline: {str(case_inputs.get("slide_outline", ""))[:6000]}
Team constraints: {str(case_inputs.get("team_constraints", ""))[:2000]}

Brief context:
{json.dumps(prep.get("brief", {}), ensure_ascii=False)[:12000]}

Critique context:
{json.dumps(prep.get("critique", {}), ensure_ascii=False)[:12000]}

Answers:
{json.dumps(answers, ensure_ascii=False)[:20000]}

Body summary:
{json.dumps(evidence.get("body_summary", {}), ensure_ascii=False)[:14000]}

Body quality warnings:
{json.dumps(evidence.get("body_quality_warnings", []), ensure_ascii=False)[:4000]}

Body events (recent):
{json.dumps(body_events, ensure_ascii=False)[:30000]}
"""


def _persist_live_evidence(evidence: dict[str, Any], data_dir: Path) -> tuple[Path, list[str]]:
    warnings: list[str] = []
    safe_session_id = _safe_session_id(str(evidence.get("session_id", "")))
    session_dir = data_dir / "live_sessions" / safe_session_id
    try:
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        body_events = _coerce_dict_list(evidence.get("body_events") or evidence.get("gesture_events"))
        if not body_events:
            warnings.append("No body events were captured for this report.")
        body_log_path = session_dir / "body_events.jsonl"
        with body_log_path.open("w", encoding="utf-8") as handle:
            for item in body_events:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
        compat_log_path = session_dir / "gesture_events.jsonl"
        with compat_log_path.open("w", encoding="utf-8") as handle:
            for item in body_events:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
        return session_dir, warnings
    except OSError as exc:
        warnings.append(f"Could not persist live evidence files: {exc}")
        return session_dir, warnings


def _write_report_file(session_dir: Path, report: dict[str, Any]) -> None:
    try:
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        return


def _safe_session_id(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", (value or "").strip())
    return cleaned or "session"


def _fallback_report(evidence: dict[str, Any], local_report: dict[str, Any] | None = None) -> dict[str, Any]:
    local = local_report if isinstance(local_report, dict) else {}
    answers = _coerce_dict_list(evidence.get("answers"))
    answer_scores = [_answer_score(answer, index) for index, answer in enumerate(answers)]
    best_index = answer_scores.index(max(answer_scores)) if answer_scores else 0
    weakest_index = answer_scores.index(min(answer_scores)) if answer_scores else 0
    best_answer = answers[best_index] if answers else {}
    weakest_answer = answers[weakest_index] if answers else {}
    body_metrics = _body_metrics_from_evidence(evidence)
    body_movement = _body_movement_from_evidence(evidence, body_metrics)
    content_improvements = _content_improvements_from_evidence(evidence, weakest_answer)
    tangible = content_improvements + _movement_improvements_from_evidence(body_movement, body_metrics)
    slide_fix = _slide_improvement_from_evidence(evidence)
    if slide_fix:
        tangible.append(slide_fix)
    avg_wpm = _avg_number([_nested_number(answer, ("metrics", "approximateWordsPerMinute")) for answer in answers])
    fillers = int(sum(_nested_number(answer, ("metrics", "fillerWordCount")) or 0 for answer in answers))
    recommendation_score = _recommendation_score_from_evidence(evidence)
    qna_score = int(_avg_number(answer_scores) or 60)
    clarity_score = _score_from_body(body_metrics)
    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "scores": {
            "overallReadinessScore": int(recommendation_score * 0.45 + qna_score * 0.35 + clarity_score * 0.20),
            "recommendationStrengthScore": recommendation_score,
            "qnaReadinessScore": qna_score,
            "presentationClarityScore": clarity_score,
        },
        "strengths": [
            _best_answer_summary(best_answer, best_index),
            "The report was generated from a saved rehearsal evidence file with answer transcripts and observable movement metrics.",
            body_movement.get("summary") or "Movement evidence was included where available.",
        ],
        "weaknesses": [
            _weak_answer_summary(weakest_answer, weakest_index),
            body_movement.get("topRepeatedIssue") or "Movement evidence was limited, so delivery coaching should be verified manually.",
            "The next practice round should connect every answer to one metric, one assumption, and one risk trigger.",
        ],
        "missedCriteria": _missed_criteria_from_evidence(evidence, answers),
        "weakAssumptions": _weak_assumptions_from_evidence(evidence),
        "likelyJudgeConcerns": [
            "Which assumption would make the recommendation fail first?",
            "What specific metric proves success in the first 30 to 90 days?",
            "Why is this recommendation better than the closest alternative?",
        ],
        "missingMetricsOrEvidence": _missing_metrics_from_answers(answers),
        "bestAnswer": {
            "questionNumber": best_index + 1 if answers else 0,
            "summary": _answer_summary(best_answer, "No best answer recorded."),
            "score": answer_scores[best_index] if answer_scores else 60,
        },
        "weakestAnswer": {
            "questionNumber": weakest_index + 1 if answers else 0,
            "summary": _answer_summary(weakest_answer, "No weakest answer recorded."),
            "score": answer_scores[weakest_index] if answer_scores else 60,
        },
        "improvedAnswers": [
            {
                "question": str(weakest_answer.get("questionText") or weakest_answer.get("question") or "Weakest answer"),
                "suggestion": _improved_answer_from_evidence(evidence, weakest_answer),
            }
        ],
        "nextPracticePlan": _practice_plan_from_evidence(body_movement, weakest_index),
        "bodyMovement": body_movement,
        "tangibleImprovements": tangible[:6],
        "deliveryMetrics": {
            "totalFillerWords": fillers,
            "averageWordsPerMinute": int(avg_wpm or 0),
            "bodyMetrics": body_metrics,
            "note": "Generated from saved answer, body, and Teachable evidence. Metrics are observable presentation proxies only.",
        },
        "reportWarnings": _report_warnings_from_evidence(evidence, body_metrics),
    }
    if local:
        report = _coerce_report_shape(report, local)
        report["bodyMovement"] = report.get("bodyMovement") or body_movement
        report["tangibleImprovements"] = report.get("tangibleImprovements") or tangible[:6]
        report["reportWarnings"] = report.get("reportWarnings") or _report_warnings_from_evidence(evidence, body_metrics)
        return report
    return report


def _coerce_dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _summarize_gesture_events(events: list[dict[str, Any]], answers: list[dict[str, Any]]) -> dict[str, Any]:
    return _summarize_body_events(events, answers)


def _summarize_body_events(events: list[dict[str, Any]], answers: list[dict[str, Any]]) -> dict[str, Any]:
    body_items = [answer.get("metrics", {}).get("body", {}) for answer in answers if isinstance(answer.get("metrics"), dict)]
    class_counts: dict[str, int] = {}
    for item in body_items + events:
        label = _teachable_class(item)
        if label:
            class_counts[label] = class_counts.get(label, 0) + 1
    dominant = max(class_counts, key=class_counts.get) if class_counts else None
    answer_metrics = _aggregate_answer_body_metrics(answers)
    event_metrics = _aggregate_body_items(events)
    body_metrics = {**event_metrics, **{key: value for key, value in answer_metrics.items() if value not in (None, 0, 0.0, {})}}
    return {
        "eventCount": len(events),
        "dominantClass": dominant,
        "classCounts": class_counts,
        "bodyMetrics": body_metrics,
        "bodyMetricsVersion": "body_metrics_v2",
    }


def _aggregate_answer_body_metrics(answers: list[dict[str, Any]]) -> dict[str, Any]:
    bodies = [answer.get("metrics", {}).get("body", {}) for answer in answers if isinstance(answer.get("metrics"), dict)]
    bodies = [body for body in bodies if isinstance(body, dict) and body]
    return _aggregate_body_items(bodies)


def _aggregate_body_items(bodies: list[dict[str, Any]]) -> dict[str, Any]:
    bodies = [body for body in bodies if isinstance(body, dict) and body]
    if not bodies:
        return {}
    category_totals: dict[str, float] = {}
    for body in bodies:
        categories = body.get("teachableCategoryPcts") or body.get("teachable_category_pcts") or {}
        if isinstance(categories, dict):
            for key, value in categories.items():
                number = _number(value)
                if number is not None:
                    category_totals[str(key)] = category_totals.get(str(key), 0.0) + number
    return {
        "poseVisiblePct": _avg_number([_body_number(body, "poseVisiblePct", "pose_visible_pct") for body in bodies]),
        "faceVisiblePct": _avg_number([_body_number(body, "faceVisiblePct", "face_visible_pct", "faceVisible") for body in bodies]),
        "cameraFacingPct": _avg_number([_body_number(body, "cameraFacingPct", "camera_facing_pct", "cameraFacingScore", "cameraFacing") for body in bodies]),
        "postureStability": _avg_number([_body_number(body, "postureStability", "posture_stability") for body in bodies]),
        "postureAlignmentScore": _avg_number([_body_number(body, "postureAlignmentScore", "posture_alignment_score") for body in bodies]),
        "postureStabilityScore": _avg_number([_body_number(body, "postureStabilityScore", "posture_stability_score") for body in bodies]),
        "gestureRatePerMin": _avg_number([_body_number(body, "gestureRatePerMin", "gesture_rate_per_min") for body in bodies]),
        "cameraEngagementProxyPct": _avg_number([_body_number(body, "cameraEngagementProxyPct", "camera_engagement_proxy_pct") for body in bodies]),
        "handsVisiblePct": _avg_number([_body_number(body, "handsVisiblePct", "hands_visible_pct", "handsVisibleScore") for body in bodies]),
        "movementControlScore": _avg_number([_body_number(body, "movementControlScore", "movement_control_score") for body in bodies]),
        "bodyPositioningScore": _avg_number([_body_number(body, "bodyPositioningScore", "body_positioning_score") for body in bodies]),
        "hiddenHandsPct": _avg_number([_body_number(body, "hiddenHandsPct", "hidden_hands_pct") for body in bodies]),
        "armsCrossedPct": _avg_number([_body_number(body, "armsCrossedPct", "arms_crossed_pct") for body in bodies]),
        "excessiveMovementPct": _avg_number([_body_number(body, "excessiveMovementPct", "excessive_movement_pct") for body in bodies]),
        "pointingPct": _avg_number([_body_number(body, "pointingPct", "pointing_pct") for body in bodies]),
        "motionLevel": _avg_number([_body_number(body, "motionLevel", "motion_level") for body in bodies]),
        "teachableBehaviorScore": _avg_number([_body_number(body, "teachableBehaviorScore", "teachable_behavior_score") for body in bodies]),
        "teachableGoodPct": _avg_number([_body_number(body, "teachableGoodPct", "teachable_good_pct") for body in bodies]),
        "teachableCautionPct": _avg_number([_body_number(body, "teachableCautionPct", "teachable_caution_pct") for body in bodies]),
        "teachableBadPct": _avg_number([_body_number(body, "teachableBadPct", "teachable_bad_pct") for body in bodies]),
        "teachableCategoryPcts": {key: round(value / max(len(bodies), 1), 1) for key, value in category_totals.items()},
    }


def _body_metrics_from_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    summary = evidence.get("body_summary") if isinstance(evidence.get("body_summary"), dict) else {}
    if not summary:
        summary = evidence.get("gesture_summary") if isinstance(evidence.get("gesture_summary"), dict) else {}
    metrics = summary.get("bodyMetrics") if isinstance(summary.get("bodyMetrics"), dict) else {}
    if not metrics:
        metrics = _aggregate_answer_body_metrics(_coerce_dict_list(evidence.get("answers")))
    dominant = summary.get("dominantClass") or metrics.get("teachableDominantClass")
    if not dominant:
        categories = metrics.get("teachableCategoryPcts") if isinstance(metrics.get("teachableCategoryPcts"), dict) else {}
        dominant = max(categories, key=categories.get) if categories else None
    if dominant:
        metrics["teachableDominantClass"] = dominant
    return metrics


def _body_movement_from_evidence(evidence: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    dominant = metrics.get("teachableDominantClass") or "No dominant class captured"
    good = _number(metrics.get("teachableGoodPct"))
    caution = _number(metrics.get("teachableCautionPct"))
    bad = _number(metrics.get("teachableBadPct"))
    pose_visible = _number(metrics.get("poseVisiblePct"))
    face_visible = _number(metrics.get("faceVisiblePct"))
    camera_facing = _number(metrics.get("cameraFacingPct"))
    posture_score = _number(metrics.get("postureAlignmentScore")) or _number(metrics.get("postureStability"))
    hands_visible = _number(metrics.get("handsVisiblePct"))
    movement_control = _number(metrics.get("movementControlScore"))
    body_positioning = _number(metrics.get("bodyPositioningScore"))
    issue = _movement_issue(dominant, metrics)
    drill = _movement_drill(dominant, metrics)
    summary = "Movement evidence was limited."
    if dominant != "No dominant class captured":
        summary = f"Dominant movement category: {dominant}. Body positioning score: {body_positioning if body_positioning is not None else 'n/a'}."
    elif body_positioning is not None:
        summary = f"Body positioning score was {body_positioning:.0f}/100 from camera-facing, posture, hands, and movement-control estimates."
    elif pose_visible is not None:
        summary = f"Pose was visible for {pose_visible:.0f}% of captured samples."
    return {
        "summary": summary,
        "dominantClass": dominant,
        "cameraFacingPct": camera_facing,
        "faceVisiblePct": face_visible,
        "postureScore": posture_score,
        "handsVisiblePct": hands_visible,
        "movementControlScore": movement_control,
        "bodyPositioningScore": body_positioning,
        "goodPct": good,
        "cautionPct": caution,
        "badPct": bad,
        "topRepeatedIssue": issue,
        "movementDrill": drill,
        "drills": _body_drills(metrics, dominant),
    }


def _content_improvements_from_evidence(evidence: dict[str, Any], weakest_answer: dict[str, Any]) -> list[dict[str, str]]:
    question = str(weakest_answer.get("questionText") or weakest_answer.get("question") or "weakest answer")
    answer_text = str(weakest_answer.get("answerText") or weakest_answer.get("answer") or "")
    case_inputs = evidence.get("case_inputs", {}) if isinstance(evidence.get("case_inputs"), dict) else {}
    company = evidence.get("session", {}).get("company_name") or "the client"
    return [
        {
            "area": "content",
            "currentEvidence": f"Weakest answer prompt: {question}",
            "change": f"Start with a direct recommendation sentence for {company}, then give one reason and one measurable proof point.",
            "practiceDrill": "Run a 30-second answer-first rep: answer in sentence 1, evidence in sentence 2, caveat in sentence 3.",
        },
        {
            "area": "content",
            "currentEvidence": _trim_text(answer_text, "The weakest answer did not provide enough text to inspect."),
            "change": "Add one metric, one threshold, or one named assumption so judges can test the claim.",
            "practiceDrill": "Rewrite the answer with the phrase: 'We would know this is working if...'.",
        },
        {
            "area": "content",
            "currentEvidence": _trim_text(str(case_inputs.get("judging_criteria", "")), "Judging criteria were not explicit."),
            "change": "Name the judging criterion your answer satisfies before moving to implementation detail.",
            "practiceDrill": "For each judge question, say the criterion out loud and then answer it in under 45 seconds.",
        },
    ]


def _movement_improvements_from_evidence(body_movement: dict[str, Any], metrics: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "area": "delivery",
            "currentEvidence": body_movement.get("topRepeatedIssue", "Movement evidence was limited."),
            "change": "Use one intentional hand position for the main claim, then return hands to a neutral visible position.",
            "practiceDrill": body_movement.get("movementDrill", "Practice one answer with hands visible and movement reduced between claims."),
        },
        {
            "area": "delivery",
            "currentEvidence": f"Camera-facing estimate: {metrics.get('cameraFacingPct', 'n/a')}%; face visible: {metrics.get('faceVisiblePct', 'n/a')}%.",
            "change": "Center your face toward the camera before the first sentence so the recommendation lands cleanly.",
            "practiceDrill": "Before each answer, check shoulders and hands are visible, then deliver the first sentence without looking away.",
        },
        {
            "area": "delivery",
            "currentEvidence": f"Posture score: {metrics.get('postureAlignmentScore', 'n/a')}; hands visible: {metrics.get('handsVisiblePct', 'n/a')}%; movement control: {metrics.get('movementControlScore', 'n/a')}.",
            "change": "Set a stable upper-body frame, keep hands visible, and reset movement between claims.",
            "practiceDrill": "Run a 45-second answer while checking only three cues: face centered, shoulders level, hands visible.",
        },
    ]


def _slide_improvement_from_evidence(evidence: dict[str, Any]) -> dict[str, str] | None:
    slide_outline = str(evidence.get("case_inputs", {}).get("slide_outline", "")).strip()
    if not slide_outline:
        return None
    return {
        "area": "slides",
        "currentEvidence": _trim_text(slide_outline, "Slide outline provided."),
        "change": "Add a visible success metric and risk trigger to the recommendation or implementation slide.",
        "practiceDrill": "Do one slide-by-slide pass where each slide has a one-sentence 'so what' tied to the rubric.",
    }


def _practice_plan_from_evidence(body_movement: dict[str, Any], weakest_index: int) -> list[str]:
    return [
        "Minute 0-2: rewrite the opening recommendation as client + action + target + metric.",
        f"Minute 2-5: rehearse question {weakest_index + 1} twice, first in 45 seconds and then in 25 seconds.",
        "Minute 5-7: repeat the answer while keeping face centered, shoulders level, and hands visible between emphasis moments.",
        "Minute 7-9: have a teammate challenge one assumption and one implementation risk.",
        f"Minute 9-10: run the movement drill: {body_movement.get('movementDrill', 'hands visible, one gesture per claim, neutral reset between claims')}",
    ]


def _report_warnings_from_evidence(evidence: dict[str, Any], body_metrics: dict[str, Any]) -> list[str]:
    warnings: list[str] = [str(item) for item in evidence.get("body_quality_warnings", []) if str(item).strip()] if isinstance(evidence.get("body_quality_warnings"), list) else []
    if not _coerce_dict_list(evidence.get("body_events") or evidence.get("gesture_events")):
        warnings.append("No raw body events were captured; movement feedback relies on answer-level metrics only.")
    pose_visible = _number(body_metrics.get("poseVisiblePct"))
    if pose_visible is not None and pose_visible < 35:
        warnings.append("Pose visibility was low, so body-movement coaching should be treated as directional.")
    face_visible = _number(body_metrics.get("faceVisiblePct"))
    if face_visible is not None and face_visible < 35:
        warnings.append("Face visibility was low, so camera-facing feedback should be treated as directional.")
    if not body_metrics.get("teachableDominantClass") and not body_metrics.get("teachableCategoryPcts"):
        warnings.append("No Teachable Machine class distribution was captured.")
    return list(dict.fromkeys(warnings))


def _answer_score(answer: dict[str, Any], index: int) -> int:
    backend = answer.get("backendGrade") if isinstance(answer.get("backendGrade"), dict) else {}
    if backend:
        return _score(
            (_number(backend.get("content_score")) or 0) * 0.4
            + (_number(backend.get("clarity_score")) or 0) * 0.25
            + (_number(backend.get("evidence_score")) or 0) * 0.2
            + (_number(backend.get("delivery_score")) or 0) * 0.15,
            60,
        )
    text = str(answer.get("answerText") or answer.get("answer") or "")
    words = word_count(text)
    score = 48 + (12 if words >= 35 else 4) + (8 if words >= 70 else 0)
    if any(char.isdigit() for char in text):
        score += 10
    if any(term in text.lower() for term in ("because", "therefore", "we recommend", "so that")):
        score += 8
    if answer.get("followUpAnswer"):
        score += 5
    return _score(score, 60)


def _answer_summary(answer: dict[str, Any], fallback: str) -> str:
    text = str(answer.get("answerText") or answer.get("answer") or "")
    return _trim_text(text, fallback)


def _best_answer_summary(answer: dict[str, Any], index: int) -> str:
    return f"Question {index + 1} was the strongest because it gave the clearest recorded answer: {_answer_summary(answer, 'No answer text available.')}"


def _weak_answer_summary(answer: dict[str, Any], index: int) -> str:
    return f"Question {index + 1} needs the most work: {_answer_summary(answer, 'No answer text available.')}"


def _improved_answer_from_evidence(evidence: dict[str, Any], answer: dict[str, Any]) -> str:
    company = evidence.get("session", {}).get("company_name") or "the client"
    question = str(answer.get("questionText") or answer.get("question") or "this question")
    return (
        f"For '{question}', start with: 'For {company}, our recommendation is [specific action] because it improves [metric] "
        "within [timeframe]. The assumption to defend is [assumption]. If [risk trigger] happens, we would [mitigation].'"
    )


def _recommendation_score_from_evidence(evidence: dict[str, Any]) -> int:
    text = " ".join(
        [
            str(evidence.get("case_inputs", {}).get("team_recommendation", "")),
            " ".join(str(answer.get("answerText", "")) for answer in _coerce_dict_list(evidence.get("answers"))),
        ]
    )
    score = 62
    if any(char.isdigit() for char in text):
        score += 8
    if any(term in text.lower() for term in ("risk", "mitigat", "tradeoff", "downside")):
        score += 7
    if any(term in text.lower() for term in ("timeline", "pilot", "phase", "owner", "month")):
        score += 6
    return _score(score, 70)


def _score_from_body(body_metrics: dict[str, Any]) -> int:
    score = 74
    body_position = _number(body_metrics.get("bodyPositioningScore"))
    if body_position is not None:
        return _score(50 + body_position * 0.45, 74)
    posture = _number(body_metrics.get("postureStability"))
    if posture is not None:
        score += int((posture - (70 if posture > 1 else 0.7)) * (0.12 if posture > 1 else 18))
    camera = _number(body_metrics.get("cameraFacingPct"))
    if camera is not None:
        score += int((camera - 55) * 0.08)
    hands = _number(body_metrics.get("handsVisiblePct"))
    if hands is not None:
        score += int((hands - 55) * 0.08)
    movement = _number(body_metrics.get("movementControlScore"))
    if movement is not None:
        score += int((movement - 65) * 0.08)
    bad = _number(body_metrics.get("teachableBadPct"))
    if bad is not None and bad > 30:
        score -= int((bad - 30) * 0.25)
    good = _number(body_metrics.get("teachableGoodPct"))
    if good is not None and good > 40:
        score += int((good - 40) * 0.12)
    return _score(score, 74)


def _missed_criteria_from_evidence(evidence: dict[str, Any], answers: list[dict[str, Any]]) -> list[str]:
    rubric = str(evidence.get("case_inputs", {}).get("judging_criteria", ""))
    lines = [line.strip(" -*0123456789.%") for line in re.split(r"\n|;|\|", rubric) if line.strip()]
    combined = " ".join(str(answer.get("answerText", "")) for answer in answers).lower()
    missed = []
    for line in lines[:6]:
        keywords = _keywords(line)[:2]
        if keywords and not any(keyword in combined for keyword in keywords):
            missed.append(line)
    return missed[:4] or ["Rubric links were not explicit enough in every answer."]


def _weak_assumptions_from_evidence(evidence: dict[str, Any]) -> list[str]:
    brief = evidence.get("prep", {}).get("brief", {})
    if isinstance(brief, dict) and isinstance(brief.get("assumptions"), list) and brief["assumptions"]:
        return [str(item) for item in brief["assumptions"][:3]]
    return [
        "Customer or stakeholder adoption reaches the level needed for the recommendation to work.",
        "The team can execute the proposed implementation within the stated time and resource constraints.",
        "The main success metric is measurable within the first practice or pilot period.",
    ]


def _missing_metrics_from_answers(answers: list[dict[str, Any]]) -> list[str]:
    missing = []
    for index, answer in enumerate(answers[:5]):
        text = str(answer.get("answerText", ""))
        if not any(char.isdigit() for char in text):
            missing.append(f"Question {index + 1}: add a number, range, or decision threshold.")
    return missing[:4] or ["Metrics were present, but tie each one to a go/no-go decision threshold."]


def _movement_issue(dominant: str, metrics: dict[str, Any]) -> str:
    if dominant in {"Hands too low / hidden", "Arms crossed", "Excessive movement", "Pointing"}:
        return f"Repeated movement category: {dominant}."
    camera = _number(metrics.get("cameraFacingPct"))
    if camera is not None and camera < 45:
        return f"Camera-facing estimate was low at {camera:.0f}%."
    posture = _number(metrics.get("postureAlignmentScore"))
    if posture is not None and posture < 60:
        return f"Posture alignment score was low at {posture:.0f}/100."
    hands = _number(metrics.get("handsVisiblePct"))
    if hands is not None and hands < 50:
        return f"Hands-visible estimate was low at {hands:.0f}%."
    movement = _number(metrics.get("movementControlScore"))
    if movement is not None and movement < 55:
        return f"Movement-control score was low at {movement:.0f}/100."
    bad = _number(metrics.get("teachableBadPct"))
    if bad is not None and bad > 30:
        return f"Teachable bad/caution movement share was elevated at {bad:.0f}%."
    return "No major repeated movement issue was captured."


def _movement_drill(dominant: str, metrics: dict[str, Any]) -> str:
    if dominant == "Hands too low / hidden":
        return "Run three 30-second answers with hands visible at chest height during the recommendation sentence."
    if dominant == "Arms crossed":
        return "Practice the opening answer with arms uncrossed and palms neutral before every key claim."
    if dominant == "Excessive movement":
        return "Plant your feet, gesture once per claim, then reset hands to neutral for two seconds."
    if dominant == "Pointing":
        return "Replace repeated pointing with open-palmed emphasis on only the metric and risk sentence."
    return "Practice one intentional gesture per claim, then return hands to a visible neutral position."


def _body_drills(metrics: dict[str, Any], dominant: str) -> list[str]:
    return [
        f"Camera-facing drill: deliver the first answer sentence with your face centered toward the camera; current estimate is {metrics.get('cameraFacingPct', 'n/a')}%.",
        f"Posture/framing drill: check shoulders are level and upper body is in frame before speaking; current posture score is {metrics.get('postureAlignmentScore', 'n/a')}.",
        f"Hands/movement drill: keep hands visible at mid-torso and reset after emphasis; current hands-visible estimate is {metrics.get('handsVisiblePct', 'n/a')}%.",
        _movement_drill(dominant, metrics),
    ]


def _teachable_class(item: dict[str, Any]) -> str | None:
    for key in ("teachableDominantClass", "teachable_dominant_class", "teachableTopClass", "teachable_top_class", "dominantClass"):
        value = item.get(key)
        if value:
            return str(value)
    return None


def _body_number(body: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = body.get(key)
        if isinstance(value, bool):
            return 100.0 if value else 0.0
        number = _number(value)
        if number is not None:
            return number
    return None


def _nested_number(item: dict[str, Any], path: tuple[str, ...]) -> float | None:
    value: Any = item
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return _number(value)


def _number(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _avg_number(values: list[object]) -> float:
    clean = [_number(value) for value in values]
    clean = [value for value in clean if value is not None]
    return round(sum(clean) / len(clean), 1) if clean else 0.0


def _trim_text(text: str, fallback: str, limit: int = 220) -> str:
    clean = " ".join(str(text or "").split())
    if not clean:
        return fallback
    return clean if len(clean) <= limit else f"{clean[: limit - 3]}..."


def _coerce_report_shape(candidate: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    merged = {**fallback, **candidate}
    fallback_scores = fallback.get("scores") if isinstance(fallback.get("scores"), dict) else {}
    candidate_scores = candidate.get("scores") if isinstance(candidate.get("scores"), dict) else {}
    merged["scores"] = {**fallback_scores, **candidate_scores}
    for key in (
        "strengths",
        "weaknesses",
        "missedCriteria",
        "weakAssumptions",
        "likelyJudgeConcerns",
        "missingMetricsOrEvidence",
        "nextPracticePlan",
    ):
        merged[key] = _coerce_strings(merged.get(key), _coerce_strings(fallback.get(key), []))
    if not isinstance(merged.get("improvedAnswers"), list) or not merged["improvedAnswers"]:
        merged["improvedAnswers"] = fallback.get("improvedAnswers", [])
    if not isinstance(merged.get("bestAnswer"), dict):
        merged["bestAnswer"] = fallback.get("bestAnswer", {})
    if not isinstance(merged.get("weakestAnswer"), dict):
        merged["weakestAnswer"] = fallback.get("weakestAnswer", {})
    if not isinstance(merged.get("deliveryMetrics"), dict):
        merged["deliveryMetrics"] = fallback.get("deliveryMetrics", {})
    if not isinstance(merged.get("bodyMovement"), dict):
        merged["bodyMovement"] = fallback.get("bodyMovement", {})
    if not isinstance(merged.get("tangibleImprovements"), list) or not merged["tangibleImprovements"]:
        merged["tangibleImprovements"] = fallback.get("tangibleImprovements", [])
    if not isinstance(merged.get("reportWarnings"), list):
        merged["reportWarnings"] = fallback.get("reportWarnings", [])
    return merged


def _coerce_strings(value: object, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return fallback
    output = [str(item).strip() for item in value if str(item).strip()]
    return output or fallback


def _score(value: object, fallback: int) -> int:
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return fallback


def _assert_live_safety(result: LiveGradeResponse) -> None:
    text = json.dumps(result.model_dump()).lower()
    banned = [
        "looked nervous",
        "nervous",
        "personality",
        "confidence",
        "authority",
        "attractive",
        "attractiveness",
        "professionalism",
        "unprofessional",
        "protected trait",
        "will win",
        "winner",
    ]
    for phrase in banned:
        if phrase in text:
            raise ValueError(f"Unsafe live feedback language detected: {phrase}")


def _assert_report_safety(report: dict[str, Any]) -> None:
    text = json.dumps(report).lower()
    banned = [
        "looked nervous",
        "nervous",
        "personality",
        "confidence",
        "authority",
        "attractive",
        "attractiveness",
        "professionalism",
        "unprofessional",
        "protected trait",
        "will win",
        "winner",
    ]
    for phrase in banned:
        if phrase in text:
            raise ValueError(f"Unsafe report language detected: {phrase}")
