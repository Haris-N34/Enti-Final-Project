const API_BASE = "http://localhost:8000";
const fallbackQuestions = [
  "What is your recommendation in one sentence?",
  "Which assumption would break your recommendation first?",
  "What metric proves success within the first 30 to 90 days?",
  "Why is this option better than the strongest alternative?",
  "What implementation risk would you mitigate first?",
  "What market evidence supports your target customer choice?"
];

const fillerWords = ["um", "uh", "like", "you know", "basically", "so", "right", "sort of", "kind of"];
let questions = [...fallbackQuestions];
let questionIndex = 0;
let transcript = "";
let recognition = null;
let startedAt = null;
let timerHandle = null;
let cameraStream = null;
let poseLandmarker = null;
let poseLoop = null;
let motionCanvas = null;
let previousPoseSample = null;
let previousFrameSample = null;
let poseSamples = [];
let lastPoseTrackAt = 0;
let latestPrep = { market_context: [], market_sources: [] };
let transcriptSource = "Idle";
let deepgramSocket = null;
let deepgramRecorder = null;
let deepgramFinalTranscript = "";
let deepgramInterimTranscript = "";
let audioStream = null;
let audioContext = null;
let audioAnalyser = null;
let audioData = null;
let audioSamples = [];
let audioLoop = null;

const $ = (id) => document.getElementById(id);

function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.classList.add("show");
  window.setTimeout(() => el.classList.remove("show"), 2600);
}

function words(text) {
  return (text.match(/[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?/g) || []).length;
}

function fillers(text) {
  const lower = ` ${text.toLowerCase()} `;
  return fillerWords.reduce((total, filler) => {
    const pattern = new RegExp(`\\b${filler.replace(" ", "\\s+")}\\b`, "g");
    return total + (lower.match(pattern) || []).length;
  }, 0);
}

function elapsedSeconds() {
  return startedAt ? Math.max(1, Math.round((Date.now() - startedAt) / 1000)) : 0;
}

function formatTime(seconds) {
  const minutes = String(Math.floor(seconds / 60)).padStart(2, "0");
  const rest = String(seconds % 60).padStart(2, "0");
  return `${minutes}:${rest}`;
}

function updateMetrics() {
  const elapsed = elapsedSeconds();
  const wordCount = words(transcript);
  $("timer").textContent = formatTime(elapsed);
  $("wordCount").textContent = wordCount;
  $("fillerCount").textContent = fillers(transcript);
  $("wpm").textContent = elapsed ? Math.round((wordCount / elapsed) * 60) : 0;
  updateBodyMetricCards();
  updateVoiceMetricCards();
}

function renderQuestion() {
  $("questionLabel").textContent = `Question ${questionIndex + 1} of ${questions.length}`;
  $("currentQuestion").textContent = questions[questionIndex] || "No question ready.";
  $("questionProgress").style.width = `${Math.round((questionIndex / Math.max(questions.length, 1)) * 100)}%`;
}

function renderPrep(data) {
  $("prepOutput").innerHTML = [
    card("Slide Summary", data.slide_summary || []),
    card("Market Context", data.market_context || []),
    card("Likely Questions", data.likely_judge_questions || [])
  ].join("");
}

function card(title, items) {
  return `
    <div class="panel">
      <h2>${escapeHtml(title)}</h2>
      <ul class="mini-list">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </div>
  `;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function prepare() {
  const payload = {
    company: $("company").value,
    industry: $("industry").value,
    case_prompt: $("casePrompt").value,
    slide_text: $("slideText").value,
    presentation_minutes: 10
  };

  try {
    const response = await fetch(`${API_BASE}/api/live/prepare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) throw new Error(`Backend returned ${response.status}`);
    const data = await response.json();
    latestPrep = data;
    questions = data.likely_judge_questions?.length ? data.likely_judge_questions : fallbackQuestions;
    questionIndex = 0;
    renderPrep(data);
    renderQuestion();
    toast(data.warnings?.length ? data.warnings[0] : "Prepared with backend.");
  } catch (error) {
    const fallback = localPrepare(payload);
    latestPrep = fallback;
    questions = fallback.likely_judge_questions;
    questionIndex = 0;
    renderPrep(fallback);
    renderQuestion();
    toast("Backend unavailable; using local fallback.");
  }
}

function localPrepare(payload) {
  const company = payload.company || "the client";
  return {
    slide_summary: [
      "Slides will be judged on recommendation clarity, evidence, metrics, risks, and implementation.",
      "Make sure the opening states the decision before detailed analysis.",
      "Use the slide text to connect each claim to the case prompt."
    ],
    market_context: [
      `Verify current market size, buyer pain points, and competitor response for ${company}.`,
      "Use only sourced numbers in the real presentation; label unsourced estimates as assumptions.",
      "Prepare one external trend and one customer/stakeholder insight."
    ],
    likely_judge_questions: fallbackQuestions
  };
}

async function startAnswering() {
  stopLiveCapture();
  window.clearInterval(timerHandle);
  transcript = "";
  deepgramFinalTranscript = "";
  deepgramInterimTranscript = "";
  audioSamples = [];
  poseSamples = [];
  previousPoseSample = null;
  previousFrameSample = null;
  lastPoseTrackAt = 0;
  $("transcriptBox").textContent = "";
  startedAt = Date.now();
  $("micDot").classList.add("on");
  timerHandle = window.setInterval(updateMetrics, 400);

  transcriptSource = "Deepgram";
  const deepgramStarted = await startDeepgramTranscription();
  if (deepgramStarted) {
    toast("Listening with Deepgram.");
    return;
  }
  startBrowserRecognition();
}

function startBrowserRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    transcriptSource = "Manual";
    toast("Speech recognition is unavailable in this browser. Type/paste your answer into the transcript box after speaking.");
    updateMetrics();
    return;
  }
  transcriptSource = "Browser";
  $("micDot").classList.add("on");
  recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = "en-US";
  recognition.onresult = (event) => {
    transcript = Array.from(event.results)
      .map((result) => result[0].transcript)
      .join(" ")
      .trim();
    $("transcriptBox").textContent = transcript || "Listening...";
    updateMetrics();
  };
  recognition.onerror = () => {
    transcriptSource = "Manual";
    toast("Mic transcription failed. You can still paste your answer and grade it.");
    updateMetrics();
  };
  recognition.onend = () => $("micDot").classList.remove("on");
  recognition.start();
  toast("Listening...");
}

async function stopAndGrade() {
  stopLiveCapture();
  $("micDot").classList.remove("on");
  window.clearInterval(timerHandle);
  updateMetrics();

  const answer = transcript || $("transcriptBox").textContent.trim();
  if (!answer || answer === "Your transcript will appear here.") {
    toast("No answer captured yet.");
    return;
  }

  const payload = {
    question: questions[questionIndex],
    answer,
    slide_text: $("slideText").value,
    case_prompt: $("casePrompt").value,
    market_context: latestPrep.market_context || [],
    market_sources: latestPrep.market_sources || [],
    metrics: collectMetrics(),
    elapsed_seconds: elapsedSeconds()
  };

  try {
    const response = await fetch(`${API_BASE}/api/live/grade-answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) throw new Error(`Backend returned ${response.status}`);
    renderGrade(await response.json());
  } catch (error) {
    renderGrade(localGrade(payload));
    toast("Backend unavailable; using local grading.");
  }
}

function localGrade(payload) {
  const count = words(payload.answer);
  const fillerCount = fillers(payload.answer);
  const wpm = payload.elapsed_seconds ? Math.round((count / payload.elapsed_seconds) * 60) : 0;
  const delivery = localDeliveryScore(payload.metrics || {}, wpm, fillerCount);
  return {
    content_score: Math.min(95, 50 + (count > 35 ? 20 : 5)),
    clarity_score: Math.max(25, Math.min(95, 75 - fillerCount * 3 + (wpm >= 90 && wpm <= 175 ? 10 : -10))),
    evidence_score: /\d|%|\$|metric|revenue|cost|margin/i.test(payload.answer) ? 80 : 52,
    delivery_score: delivery,
    metrics: { ...(payload.metrics || {}), word_count: count, filler_word_count: fillerCount, estimated_wpm: wpm },
    feedback: [
      "Lead with the direct answer.",
      "Add one concrete metric or threshold.",
      "Name the biggest risk and your mitigation."
    ],
    follow_up_question: "What evidence would convince a skeptical judge?"
  };
}

async function startDeepgramTranscription() {
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder || !window.WebSocket) {
    transcriptSource = "Browser";
    return false;
  }
  try {
    audioStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    startAudioMeter(audioStream);
    deepgramSocket = await openDeepgramConnection();
    deepgramSocket.onmessage = handleDeepgramMessage;
    deepgramSocket.onclose = () => {
      if (transcriptSource === "Deepgram") $("micDot").classList.remove("on");
    };
    startDeepgramRecorder();
    transcriptSource = "Deepgram";
    updateMetrics();
    return true;
  } catch (error) {
    stopLiveCapture();
    transcriptSource = "Browser";
    updateMetrics();
    return false;
  }
}

async function openDeepgramConnection() {
  const url =
    "wss://api.deepgram.com/v1/listen?model=nova-3&smart_format=true&interim_results=true&utterances=true&diarize=true&punctuate=true";
  try {
    const tokenResponse = await fetch(`${API_BASE}/api/live/deepgram-token`, { method: "POST" });
    if (tokenResponse.ok) {
      const tokenData = await tokenResponse.json();
      if (tokenData.access_token) {
        return await openDeepgramSocket(tokenData.access_token, url);
      }
    }
  } catch (error) {
    // The backend proxy below is the durable path when temporary-token auth is unavailable.
  }
  return openBackendDeepgramProxy();
}

async function openDeepgramSocket(token, url) {
  try {
    return await tryDeepgramSocket(url, ["bearer", token]);
  } catch (error) {
    try {
      return await tryDeepgramSocket(url, ["token", token]);
    } catch (fallbackError) {
      return tryDeepgramSocket(`${url}&token=${encodeURIComponent(token)}`);
    }
  }
}

function tryDeepgramSocket(url, protocols) {
  return new Promise((resolve, reject) => {
    let settled = false;
    const socket = protocols ? new WebSocket(url, protocols) : new WebSocket(url);
    const timer = window.setTimeout(() => {
      if (settled) return;
      settled = true;
      socket.close();
      reject(new Error("Deepgram WebSocket timed out"));
    }, 3500);
    socket.onopen = () => {
      if (settled) return;
      settled = true;
      window.clearTimeout(timer);
      resolve(socket);
    };
    socket.onerror = () => {
      if (settled) return;
      settled = true;
      window.clearTimeout(timer);
      socket.close();
      reject(new Error("Deepgram WebSocket failed"));
    };
    socket.onclose = () => {
      if (settled) return;
      settled = true;
      window.clearTimeout(timer);
      reject(new Error("Deepgram WebSocket closed before opening"));
    };
  });
}

function openBackendDeepgramProxy() {
  const wsBase = API_BASE.replace(/^http/i, "ws");
  return tryDeepgramSocket(`${wsBase}/api/live/deepgram-proxy`);
}

function startDeepgramRecorder() {
  if (!audioStream || !deepgramSocket) throw new Error("Audio stream is not ready");
  const preferred = "audio/webm;codecs=opus";
  const options = MediaRecorder.isTypeSupported(preferred) ? { mimeType: preferred } : {};
  deepgramRecorder = new MediaRecorder(audioStream, options);
  deepgramRecorder.ondataavailable = (event) => {
    if (event.data?.size && deepgramSocket?.readyState === WebSocket.OPEN) {
      deepgramSocket.send(event.data);
    }
  };
  deepgramRecorder.start(250);
}

function handleDeepgramMessage(event) {
  let data = null;
  try {
    data = JSON.parse(event.data);
  } catch (error) {
    return;
  }
  if (data.type === "error") {
    toast(data.message || "Deepgram stream failed; using browser speech fallback.");
    stopLiveCapture();
    startBrowserRecognition();
    return;
  }
  if (data.type && data.type !== "Results") return;
  const text = data.channel?.alternatives?.[0]?.transcript?.trim();
  if (!text) return;
  if (data.is_final || data.speech_final) {
    deepgramFinalTranscript = `${deepgramFinalTranscript} ${text}`.trim();
    deepgramInterimTranscript = "";
  } else {
    deepgramInterimTranscript = text;
  }
  transcript = `${deepgramFinalTranscript} ${deepgramInterimTranscript}`.trim();
  $("transcriptBox").textContent = transcript || "Listening...";
  updateMetrics();
}

function startAudioMeter(stream) {
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (!AudioContext) return;
  audioContext = new AudioContext();
  const source = audioContext.createMediaStreamSource(stream);
  audioAnalyser = audioContext.createAnalyser();
  audioAnalyser.fftSize = 2048;
  audioData = new Uint8Array(audioAnalyser.fftSize);
  source.connect(audioAnalyser);
  sampleAudio();
}

function sampleAudio() {
  if (!audioAnalyser || !audioData) return;
  audioAnalyser.getByteTimeDomainData(audioData);
  let sumSquares = 0;
  for (const value of audioData) {
    const centered = (value - 128) / 128;
    sumSquares += centered * centered;
  }
  const energy = Math.sqrt(sumSquares / audioData.length);
  audioSamples.push({ at: performance.now(), energy });
  if (audioSamples.length > 1800) audioSamples.shift();
  audioLoop = window.requestAnimationFrame(sampleAudio);
}

function stopLiveCapture() {
  if (recognition) {
    try {
      recognition.stop();
    } catch (error) {
      // Ignore duplicate stop calls from browser speech recognition.
    }
    recognition = null;
  }
  if (deepgramRecorder && deepgramRecorder.state !== "inactive") {
    try {
      deepgramRecorder.stop();
    } catch (error) {
      // MediaRecorder may already be stopped during fallback.
    }
  }
  deepgramRecorder = null;
  if (deepgramSocket && deepgramSocket.readyState <= WebSocket.OPEN) {
    try {
      if (deepgramSocket.readyState === WebSocket.OPEN) {
        deepgramSocket.send(JSON.stringify({ type: "CloseStream" }));
      }
      deepgramSocket.close();
    } catch (error) {
      // Closing a socket is best-effort during stop/reset.
    }
  }
  deepgramSocket = null;
  if (audioStream) {
    audioStream.getTracks().forEach((track) => track.stop());
    audioStream = null;
  }
  if (audioLoop) {
    window.cancelAnimationFrame(audioLoop);
    audioLoop = null;
  }
  if (audioContext) {
    audioContext.close().catch(() => {});
    audioContext = null;
  }
  audioAnalyser = null;
  audioData = null;
  $("micDot").classList.remove("on");
}

function renderGrade(data) {
  $("gradeOutput").innerHTML = `
    <h2>Live Grade</h2>
    <div class="grid three-col">
      ${score("Content", data.content_score)}
      ${score("Clarity", data.clarity_score)}
      ${score("Evidence", data.evidence_score)}
      ${score("Delivery", data.delivery_score || 0)}
    </div>
    ${metricSummary(data.metrics || {})}
    <h3>Feedback</h3>
    <ul class="mini-list">${(data.feedback || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    <h3>Adaptive follow-up</h3>
    <p>${escapeHtml(data.follow_up_question)}</p>
  `;
}

function score(label, value) {
  return `<div class="score-card"><span>${label}</span><strong>${value}/100</strong><div class="score-track"><span style="width:${value}%"></span></div></div>`;
}

function nextQuestion() {
  questionIndex = Math.min(questionIndex + 1, questions.length - 1);
  stopLiveCapture();
  window.clearInterval(timerHandle);
  transcript = "";
  deepgramFinalTranscript = "";
  deepgramInterimTranscript = "";
  audioSamples = [];
  poseSamples = [];
  previousPoseSample = null;
  previousFrameSample = null;
  lastPoseTrackAt = 0;
  startedAt = null;
  transcriptSource = "Idle";
  $("transcriptBox").textContent = "Your transcript will appear here.";
  updateMetrics();
  renderQuestion();
}

async function enableCamera() {
  if (!navigator.mediaDevices?.getUserMedia) {
    toast("Camera preview is unavailable in this browser.");
    return;
  }
  try {
    cameraStream = cameraStream || (await navigator.mediaDevices.getUserMedia({ video: true, audio: false }));
    $("camera").srcObject = cameraStream;
    await setupPoseTracking();
    toast(poseLandmarker ? "Camera and body tracking enabled." : "Camera enabled. Pose model unavailable; using motion tracking.");
  } catch (error) {
    toast("Camera permission blocked or unavailable.");
  }
}

function reset() {
  stopLiveCapture();
  if (cameraStream) cameraStream.getTracks().forEach((track) => track.stop());
  if (poseLoop) window.cancelAnimationFrame(poseLoop);
  window.location.reload();
}

async function setupPoseTracking() {
  if (poseLoop) return;
  await tryLoadPoseLandmarker();
  poseLoop = window.requestAnimationFrame(trackPose);
}

async function tryLoadPoseLandmarker() {
  if (poseLandmarker) return;
  const version = "0.10.35";
  try {
    const vision = await import(`https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${version}/vision_bundle.mjs`);
    const fileset = await vision.FilesetResolver.forVisionTasks(
      `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${version}/wasm`
    );
    poseLandmarker = await createPoseLandmarker(vision, fileset, "GPU");
  } catch (gpuError) {
    try {
      const vision = await import(`https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${version}/vision_bundle.mjs`);
      const fileset = await vision.FilesetResolver.forVisionTasks(
        `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${version}/wasm`
      );
      poseLandmarker = await createPoseLandmarker(vision, fileset, "CPU");
    } catch (cpuError) {
      console.warn("Pose tracking failed to load", cpuError);
      poseLandmarker = null;
    }
  }
}

function createPoseLandmarker(vision, fileset, delegate) {
  return vision.PoseLandmarker.createFromOptions(fileset, {
    baseOptions: {
      modelAssetPath:
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task",
      delegate
    },
    runningMode: "VIDEO",
    numPoses: 1,
    minPoseDetectionConfidence: 0.35,
    minPosePresenceConfidence: 0.35,
    minTrackingConfidence: 0.35
  });
}

function trackPose() {
  const video = $("camera");
  if (!video || video.readyState < 2) {
    poseLoop = window.requestAnimationFrame(trackPose);
    return;
  }
  const now = performance.now();
  if (now - lastPoseTrackAt < 120) {
    poseLoop = window.requestAnimationFrame(trackPose);
    return;
  }
  lastPoseTrackAt = now;

  const canvas = $("poseCanvas");
  const ctx = canvas.getContext("2d");
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 360;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  let pose = null;
  if (poseLandmarker) {
    try {
      const result = poseLandmarker.detectForVideo(video, now);
      pose = result.landmarks?.[0] || null;
    } catch (error) {
      console.warn("Pose frame detection failed", error);
      pose = null;
    }
  }

  const sample = pose ? samplePoseMetrics(pose, canvas) : sampleMotionMetrics(video, canvas);
  poseSamples.push(sample);
  if (poseSamples.length > 900) poseSamples.shift();
  drawPose(ctx, pose, canvas);
  updateBodyMetricCards();
  poseLoop = window.requestAnimationFrame(trackPose);
}

function samplePoseMetrics(landmarks, canvas) {
  const now = performance.now();
  const leftShoulder = landmarks[11];
  const rightShoulder = landmarks[12];
  const leftWrist = landmarks[15];
  const rightWrist = landmarks[16];
  const nose = landmarks[0];
  const center = midpoint(leftShoulder, rightShoulder);
  const shoulderTilt = Math.abs((leftShoulder.y - rightShoulder.y) * 100);
  const shoulderWidth = Math.max(distance(leftShoulder, rightShoulder), 0.001);
  const wristMotion = previousPoseSample
    ? (distance(leftWrist, previousPoseSample.leftWrist) + distance(rightWrist, previousPoseSample.rightWrist)) / shoulderWidth
    : 0;
  const centerMotion = previousPoseSample ? distance(center, previousPoseSample.center) / shoulderWidth : 0;
  const shoulderLeft = Math.min(leftShoulder.x, rightShoulder.x);
  const shoulderRight = Math.max(leftShoulder.x, rightShoulder.x);
  const shoulderMidY = (leftShoulder.y + rightShoulder.y) / 2;
  const cameraProxy =
    nose &&
    leftShoulder &&
    rightShoulder &&
    nose.visibility > 0.45 &&
    nose.y < shoulderMidY &&
    nose.x > shoulderLeft - shoulderWidth * 0.35 &&
    nose.x < shoulderRight + shoulderWidth * 0.35
      ? 1
      : 0;
  previousPoseSample = { leftWrist, rightWrist, center };
  return {
    at: now,
    poseVisible: 1,
    postureMovement: centerMotion,
    shoulderTilt,
    gestureMotion: wristMotion,
    motionLevel: wristMotion + centerMotion,
    cameraProxy
  };
}

function sampleMotionMetrics(video, canvas) {
  const now = performance.now();
  motionCanvas = motionCanvas || document.createElement("canvas");
  motionCanvas.width = 96;
  motionCanvas.height = 54;
  const ctx = motionCanvas.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(video, 0, 0, motionCanvas.width, motionCanvas.height);
  const frame = ctx.getImageData(0, 0, 96, 54).data;
  let delta = 0;
  if (previousFrameSample) {
    for (let i = 0; i < frame.length; i += 16) {
      delta += Math.abs(frame[i] - previousFrameSample[i]);
    }
    delta /= frame.length / 16;
  }
  previousFrameSample = new Uint8ClampedArray(frame);
  return {
    at: now,
    poseVisible: 0,
    postureMovement: delta / 255,
    shoulderTilt: null,
    gestureMotion: delta / 255,
    motionLevel: delta / 255,
    cameraProxy: null
  };
}

function collectMetrics() {
  const elapsed = elapsedSeconds();
  const wordCount = words(transcript);
  return {
    word_count: wordCount,
    filler_word_count: fillers(transcript),
    estimated_wpm: elapsed ? Math.round((wordCount / elapsed) * 60) : 0,
    elapsed_seconds: elapsed,
    ...summarizePoseSamples(),
    ...summarizeAudioSamples()
  };
}

function summarizePoseSamples() {
  if (!poseSamples.length) {
    return {};
  }
  const poseVisiblePct = percent(avg(poseSamples.map((sample) => sample.poseVisible)));
  const movement = avg(poseSamples.map((sample) => sample.postureMovement || 0));
  const hasPoseSamples = poseSamples.some((sample) => sample.poseVisible === 1);
  const gestureThreshold = hasPoseSamples ? 0.08 : 0.01;
  const gestureEvents = poseSamples.filter((sample) => (sample.gestureMotion || 0) > gestureThreshold).length;
  const minutes = Math.max(elapsedSeconds() / 60, 1 / 60);
  const cameraValues = poseSamples.map((sample) => sample.cameraProxy).filter((value) => value !== null);
  return {
    pose_visible_pct: Math.round(poseVisiblePct),
    posture_stability: round2(Math.max(0, Math.min(1, 1 - movement * 7))),
    shoulder_tilt_avg: round2(avg(poseSamples.map((sample) => sample.shoulderTilt).filter((value) => value !== null))),
    gesture_rate_per_min: Math.round(gestureEvents / minutes),
    motion_level: round2(avg(poseSamples.map((sample) => sample.motionLevel || 0))),
    camera_engagement_proxy_pct: cameraValues.length ? Math.round(percent(avg(cameraValues))) : null
  };
}

function updateBodyMetricCards() {
  const summary = summarizePoseSamples();
  $("poseVisible").textContent = `${summary.pose_visible_pct || 0}%`;
  $("postureStability").textContent = summary.posture_stability ?? 0;
  $("gestureRate").textContent = summary.gesture_rate_per_min ?? 0;
  $("engagementProxy").textContent =
    summary.camera_engagement_proxy_pct === null || summary.camera_engagement_proxy_pct === undefined
      ? "n/a"
      : `${summary.camera_engagement_proxy_pct}%`;
}

function summarizeAudioSamples() {
  if (!audioSamples.length) {
    return {};
  }
  const energies = audioSamples.map((sample) => sample.energy).filter((value) => Number.isFinite(value));
  const mean = avg(energies);
  const variance = avg(energies.map((value) => (value - mean) ** 2));
  const silencePct = percent(energies.filter((value) => value < 0.012).length / Math.max(energies.length, 1));
  return {
    audio_energy_avg: round3(mean),
    audio_energy_variation: round3(Math.sqrt(variance)),
    silence_pct: Math.round(silencePct)
  };
}

function updateVoiceMetricCards() {
  const summary = summarizeAudioSamples();
  $("audioEnergy").textContent = summary.audio_energy_avg === undefined ? "n/a" : Math.round(summary.audio_energy_avg * 100);
  $("audioVariation").textContent =
    summary.audio_energy_variation === undefined ? "n/a" : Math.round(summary.audio_energy_variation * 100);
  $("silencePct").textContent = summary.silence_pct === undefined ? "n/a" : `${summary.silence_pct}%`;
  $("transcriptSource").textContent = transcriptSource;
}

function drawPose(ctx, landmarks, canvas) {
  if (!landmarks) return;
  const points = [0, 11, 12, 13, 14, 15, 16, 23, 24].map((index) => landmarks[index]).filter(Boolean);
  ctx.fillStyle = "#6ee7d8";
  for (const point of points) {
    ctx.beginPath();
    ctx.arc(point.x * canvas.width, point.y * canvas.height, 4, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.strokeStyle = "#f2b84b";
  ctx.lineWidth = 2;
  connect(ctx, canvas, landmarks[11], landmarks[12]);
  connect(ctx, canvas, landmarks[11], landmarks[13]);
  connect(ctx, canvas, landmarks[13], landmarks[15]);
  connect(ctx, canvas, landmarks[12], landmarks[14]);
  connect(ctx, canvas, landmarks[14], landmarks[16]);
}

function connect(ctx, canvas, a, b) {
  if (!a || !b) return;
  ctx.beginPath();
  ctx.moveTo(a.x * canvas.width, a.y * canvas.height);
  ctx.lineTo(b.x * canvas.width, b.y * canvas.height);
  ctx.stroke();
}

function midpoint(a, b) {
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
}

function distance(a, b) {
  if (!a || !b) return 0;
  return Math.hypot(a.x - b.x, a.y - b.y);
}

function avg(values) {
  const clean = values.filter((value) => Number.isFinite(value));
  return clean.length ? clean.reduce((total, value) => total + value, 0) / clean.length : 0;
}

function percent(value) {
  return Math.max(0, Math.min(100, value * 100));
}

function round2(value) {
  return Math.round((Number.isFinite(value) ? value : 0) * 100) / 100;
}

function round3(value) {
  return Math.round((Number.isFinite(value) ? value : 0) * 1000) / 1000;
}

function localDeliveryScore(metrics, wpm, fillerCount) {
  let value = 78;
  if (wpm > 185 || (wpm > 0 && wpm < 90)) value -= 10;
  value -= Math.min(fillerCount * 2, 14);
  if (metrics.posture_stability !== undefined) value += Math.round((metrics.posture_stability - 0.65) * 20);
  if (metrics.camera_engagement_proxy_pct !== null && metrics.camera_engagement_proxy_pct < 45) value -= 8;
  if (metrics.gesture_rate_per_min > 45) value -= 6;
  if (metrics.silence_pct > 45) value -= 6;
  if (metrics.audio_energy_variation !== undefined && metrics.audio_energy_variation < 0.01) value -= 4;
  return Math.max(20, Math.min(95, value));
}

function metricSummary(metrics) {
  return `
    <div class="metric-strip">
      <div class="metric"><strong>${metrics.estimated_wpm ?? 0}</strong><span>wpm</span></div>
      <div class="metric"><strong>${metrics.filler_word_count ?? 0}</strong><span>fillers</span></div>
      <div class="metric"><strong>${metrics.posture_stability ?? "n/a"}</strong><span>posture</span></div>
      <div class="metric"><strong>${metrics.gesture_rate_per_min ?? "n/a"}</strong><span>gestures/min</span></div>
      <div class="metric"><strong>${metrics.silence_pct ?? "n/a"}${metrics.silence_pct === undefined ? "" : "%"}</strong><span>low audio</span></div>
      <div class="metric"><strong>${metrics.audio_energy_variation ?? "n/a"}</strong><span>voice variation</span></div>
    </div>
  `;
}

$("slideFile").addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  $("slideText").value = await file.text();
  toast("Slide text loaded.");
});
$("prepareBtn").addEventListener("click", prepare);
$("startBtn").addEventListener("click", startAnswering);
$("stopBtn").addEventListener("click", stopAndGrade);
$("nextBtn").addEventListener("click", nextQuestion);
$("cameraBtn").addEventListener("click", enableCamera);
$("resetBtn").addEventListener("click", reset);
renderQuestion();
updateMetrics();
