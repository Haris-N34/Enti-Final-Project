from __future__ import annotations

import asyncio
import json
import re
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
    posture_stability: float | None = None
    shoulder_tilt_avg: float | None = None
    gesture_rate_per_min: float | None = None
    motion_level: float | None = None
    camera_engagement_proxy_pct: float | None = None
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
    company_name: str = ""
    case_prompt: str = ""
    judging_criteria: str = ""
    team_recommendation: str = ""
    slide_outline: str = ""
    team_constraints: str = ""
    brief: dict[str, Any] = Field(default_factory=dict)
    critique: dict[str, Any] = Field(default_factory=dict)
    answers: list[dict[str, Any]] = Field(default_factory=list)
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
    fallback = payload.local_report if isinstance(payload.local_report, dict) and payload.local_report else _fallback_report(payload)
    settings = get_settings()
    log_warning = _write_gesture_events_log(payload, settings.data_dir)
    if log_warning:
        warnings.append(log_warning)

    client = GroqClient(settings.groq_base_url, settings.groq_api_key, settings.groq_model)
    response, warning = await client.complete_json(
        prompt=_report_prompt(payload),
        system_prompt=(
            "You are a strict but helpful university case competition coach. "
            "Return JSON only. Use observable metrics and transcript evidence. "
            "Do not infer emotion, personality, protected traits, or official judging outcomes."
        ),
    )
    if warning:
        warnings.append(warning)
        return LiveReportResponse(report=fallback, warnings=warnings)
    if not isinstance(response, dict):
        warnings.append("Groq response was not a JSON object; used fallback report.")
        return LiveReportResponse(report=fallback, warnings=warnings)

    report = _coerce_report_shape(response, fallback)
    try:
        _assert_report_safety(report)
    except ValueError as exc:
        warnings.append(f"{exc}; used fallback report.")
        return LiveReportResponse(report=fallback, warnings=warnings)
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
        score += int((metrics.posture_stability - 0.65) * 20)
    if metrics.camera_engagement_proxy_pct is not None and metrics.camera_engagement_proxy_pct < 45:
        score -= 8
    if metrics.gesture_rate_per_min is not None and metrics.gesture_rate_per_min > 45:
        score -= 6
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
    if metrics.camera_engagement_proxy_pct is not None and metrics.camera_engagement_proxy_pct < 45:
        return "Your camera-facing posture proxy was low; practice the first sentence facing the camera."
    if metrics.gesture_rate_per_min is not None and metrics.gesture_rate_per_min > 45:
        return "Gesture movement was high; anchor your hands before the recommendation sentence."
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


def _report_prompt(payload: LiveReportRequest) -> str:
    gesture_events = payload.gesture_events[-1500:]
    answers = payload.answers[:5]
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
  "deliveryMetrics": {{
    "totalFillerWords": int,
    "averageWordsPerMinute": int,
    "bodyMetrics": object|null,
    "note": "..."
  }}
}}

Constraints:
- Ground report in supplied transcript answers and gesture/body observations only.
- Do not infer emotion, personality, confidence, protected traits, winner likelihood, or official judge decisions.
- Keep language practical and actionable for rehearsal.

Company: {payload.company_name}
Case prompt: {payload.case_prompt[:4000]}
Judging criteria: {payload.judging_criteria[:4000]}
Team recommendation: {payload.team_recommendation[:4000]}
Slide outline: {payload.slide_outline[:6000]}
Team constraints: {payload.team_constraints[:2000]}

Brief context:
{json.dumps(payload.brief, ensure_ascii=False)[:12000]}

Critique context:
{json.dumps(payload.critique, ensure_ascii=False)[:12000]}

Answers:
{json.dumps(answers, ensure_ascii=False)[:20000]}

Gesture summary:
{json.dumps(payload.gesture_summary, ensure_ascii=False)[:12000]}

Gesture events (recent):
{json.dumps(gesture_events, ensure_ascii=False)[:30000]}
"""


def _write_gesture_events_log(payload: LiveReportRequest, data_dir: Path) -> str | None:
    if not payload.gesture_events:
        return "No gesture events were captured for this report."
    try:
        log_dir = data_dir / "gesture_logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        safe_session_id = _safe_session_id(payload.session_id)
        log_path = log_dir / f"{safe_session_id}.jsonl"
        summary_path = log_dir / f"{safe_session_id}.summary.json"
        with log_path.open("w", encoding="utf-8") as handle:
            for item in payload.gesture_events:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
        summary = {
            "session_id": payload.session_id,
            "company_name": payload.company_name,
            "gesture_summary": payload.gesture_summary,
            "event_count": len(payload.gesture_events),
        }
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        return None
    except OSError as exc:
        return f"Could not persist gesture event log file: {exc}"


def _safe_session_id(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", (value or "").strip())
    return cleaned or "session"


def _fallback_report(payload: LiveReportRequest) -> dict[str, Any]:
    local = payload.local_report if isinstance(payload.local_report, dict) else {}
    if local:
        return local
    return {
        "generatedAt": "",
        "scores": {
            "overallReadinessScore": 60,
            "recommendationStrengthScore": 60,
            "qnaReadinessScore": 60,
            "presentationClarityScore": 60,
        },
        "strengths": ["Complete rehearsal transcript was available for report synthesis."],
        "weaknesses": ["Model-based report generation was unavailable for this run."],
        "missedCriteria": ["Report fallback was used; review rubric mapping manually."],
        "weakAssumptions": [],
        "likelyJudgeConcerns": [],
        "missingMetricsOrEvidence": [],
        "bestAnswer": {"questionNumber": 1, "summary": "No model report summary available.", "score": 60},
        "weakestAnswer": {"questionNumber": 1, "summary": "No model report summary available.", "score": 60},
        "improvedAnswers": [{"question": "Fallback", "suggestion": "Regenerate report when model access is configured."}],
        "nextPracticePlan": ["Regenerate report after configuring Groq and rerun rehearsal."],
        "deliveryMetrics": {"totalFillerWords": 0, "averageWordsPerMinute": 0, "bodyMetrics": None, "note": "Fallback report."},
    }


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
        "professionalism",
        "unprofessional",
        "protected trait",
        "will win",
        "winner",
    ]
    for phrase in banned:
        if phrase in text:
            raise ValueError(f"Unsafe report language detected: {phrase}")
