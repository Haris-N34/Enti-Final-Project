const STORAGE_KEY = "caseMirror.session.v1";

const defaultRubric = [
  "Problem framing and prompt alignment",
  "Analysis depth and evidence quality",
  "Recommendation clarity",
  "Financial or operational reasoning",
  "Implementation feasibility",
  "Risk analysis and mitigation",
  "Presentation clarity and Q&A readiness"
];

const fillerWords = [
  "um",
  "uh",
  "like",
  "basically",
  "actually",
  "literally",
  "right",
  "you know",
  "sort of",
  "kind of"
];

const sampleInput = {
  casePrompt:
    "EcoRide, a regional e-bike subscription company, is considering whether to expand from two university cities into a larger metropolitan market. The company has strong student adoption but thin margins, limited service staff, and rising battery replacement costs. Teams must recommend whether EcoRide should expand now, delay expansion, or pursue a partnership model. The client wants a 12-month plan that protects cash flow while increasing market share.",
  judgingCriteria:
    "40% strategic fit and clarity of recommendation\n25% financial and operational feasibility\n15% implementation roadmap\n10% risk mitigation\n10% presentation quality and Q&A defense",
  teamRecommendation:
    "We recommend a partnership-led expansion into one metropolitan pilot district with two anchor universities and one transit partner. EcoRide should avoid a full city launch and instead test a 12-month bundled subscription with student housing groups, campus sustainability offices, and local transit discounts. The team thinks this balances growth with lower service risk, but we still need stronger financial assumptions and a clearer explanation of battery replacement costs.",
  companyName: "EcoRide",
  industryContext:
    "Micromobility, campus transportation, subscription mobility, municipal partnerships, student adoption.",
  targetPresentationLength: "10 minutes",
  teamConstraints:
    "Four-person team, limited financial data, must present recommendation and implementation roadmap.",
  slideOutline:
    "1. Executive summary\n2. Market opportunity\n3. Options considered\n4. Recommended pilot model\n5. Financial assumptions\n6. Implementation timeline\n7. Risks and mitigations\n8. Closing recommendation"
};

const app = document.getElementById("app");
const toast = document.getElementById("toast");

const state = {
  session: loadSession(),
  setupErrors: {},
  loading: "",
  error: "",
  recognition: null,
  micActive: false,
  webcamStream: null
};

function createSession() {
  return {
    id: createId(),
    createdAt: new Date().toISOString(),
    casePrompt: "",
    judgingCriteria: "",
    teamRecommendation: "",
    companyName: "",
    industryContext: "",
    targetPresentationLength: "",
    teamConstraints: "",
    slideOutline: "",
    caseBrief: null,
    recommendationCritique: null,
    questions: [],
    answers: [],
    finalReport: null,
    timerStartedAt: null
  };
}

function createId() {
  if (window.crypto && typeof window.crypto.randomUUID === "function") {
    return window.crypto.randomUUID();
  }
  return `cm-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function loadSession() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? { ...createSession(), ...JSON.parse(saved) } : createSession();
  } catch (error) {
    return createSession();
  }
}

function saveSession() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state.session));
}

function routeFromHash() {
  const route = (window.location.hash || "#/").replace("#/", "") || "home";
  return route === "" ? "home" : route;
}

function go(route) {
  window.location.hash = route === "home" ? "#/" : `#/${route}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function nl2br(value) {
  return escapeHtml(value).replace(/\n/g, "<br />");
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2600);
}

function delay(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function withLoading(name, task) {
  state.loading = name;
  state.error = "";
  render();
  try {
    await delay(650);
    await task();
  } catch (error) {
    state.error = error.message || "Something went wrong. Try again.";
  } finally {
    state.loading = "";
    render();
  }
}

function textValue(id) {
  const element = document.getElementById(id);
  return element ? element.value.trim() : "";
}

function wordCount(text) {
  return (text.toLowerCase().match(/[a-z0-9]+(?:'[a-z0-9]+)?/g) || []).length;
}

function sentences(text) {
  return String(text || "")
    .replace(/\s+/g, " ")
    .split(/(?<=[.!?])\s+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function compactSentence(text, fallback) {
  const first = sentences(text)[0];
  if (!first) return fallback;
  return first.length > 210 ? `${first.slice(0, 207)}...` : first;
}

function extractKeywords(text, limit = 8) {
  const stop = new Set([
    "the",
    "and",
    "for",
    "that",
    "with",
    "this",
    "from",
    "into",
    "should",
    "would",
    "could",
    "have",
    "has",
    "are",
    "was",
    "were",
    "their",
    "team",
    "case",
    "recommend",
    "recommendation",
    "company",
    "business",
    "market",
    "must",
    "need",
    "needs",
    "will",
    "about",
    "because",
    "while",
    "through",
    "during",
    "within",
    "without"
  ]);

  const counts = new Map();
  const words = String(text || "")
    .toLowerCase()
    .match(/[a-z][a-z0-9-]{3,}/g) || [];

  words.forEach((word) => {
    const normalized = word.replace(/s$/, "");
    if (!stop.has(normalized)) {
      counts.set(normalized, (counts.get(normalized) || 0) + 1);
    }
  });

  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([word]) => word);
}

function parseRubric(criteria) {
  const lines = String(criteria || "")
    .split(/\n|;|\|/)
    .map((item) => item.replace(/^[-*0-9.%\s]+/, "").trim())
    .filter(Boolean);
  return lines.length ? lines.slice(0, 7) : [...defaultRubric];
}

function findDecisionLanguage(prompt) {
  const decisionSentence =
    sentences(prompt).find((sentence) => /whether|decide|choice|recommend|select|choose|evaluate/i.test(sentence)) ||
    compactSentence(prompt, "Decide which recommendation best answers the case prompt under the stated constraints.");
  return decisionSentence;
}

function generateBrief(session) {
  const company = session.companyName || "the client";
  const keywords = extractKeywords(
    `${session.casePrompt} ${session.teamRecommendation} ${session.industryContext}`,
    10
  );
  const rubric = parseRubric(session.judgingCriteria);
  const usesDefaultRubric = !session.judgingCriteria.trim();
  const recommendationStart = compactSentence(
    session.teamRecommendation,
    "The team has a draft recommendation, but the core choice should be stated more directly."
  );
  const problemSummary = `${company} is facing a case decision around ${keywords
    .slice(0, 4)
    .join(", ") || "strategy, feasibility, risk, and execution"}. ${compactSentence(
    session.casePrompt,
    "The case requires a focused recommendation that fits the prompt and constraints."
  )}`;

  return {
    usesDefaultRubric,
    problemSummary,
    keyDecision: findDecisionLanguage(session.casePrompt),
    judgePriorities: rubric.slice(0, 6).map((criterion, index) => {
      const keyword = keywords[index] || "evidence";
      return `${criterion}: show how the recommendation handles ${keyword} with specific tradeoffs.`;
    }),
    recommendationSnapshot: recommendationStart,
    strengths: [
      `The recommendation gives judges a concrete direction: ${recommendationStart}`,
      `It connects to visible case themes such as ${keywords.slice(0, 3).join(", ") || "market fit and feasibility"}.`,
      session.teamConstraints
        ? `The team has named constraints, which helps frame feasibility: ${session.teamConstraints}.`
        : "The solution can become stronger by making constraints explicit before defending the recommendation."
    ],
    gaps: [
      "The case logic needs a clearer decision rule so judges understand why this option beats alternatives.",
      "Financial, operational, or resource assumptions should be stated in plain terms instead of implied.",
      "The team should connect each major slide or answer back to the official judging criteria.",
      "Risks should be framed as tradeoffs with mitigation, not just listed near the end."
    ],
    assumptions: [
      `${company} can execute the recommendation within the target presentation constraints and available resources.`,
      `The target stakeholder or customer segment will respond to the proposed value proposition.`,
      "The expected benefits are large enough to justify implementation complexity and downside risk."
    ],
    risks: [
      {
        risk: "Implementation complexity",
        mitigation: "Name the first pilot owner, timeline, and go/no-go milestone."
      },
      {
        risk: "Weak evidence or missing metrics",
        mitigation: "Use a small set of defensible metrics and label any estimates as assumptions."
      },
      {
        risk: "Judges see the solution as too broad",
        mitigation: "Narrow the recommendation to one primary action, one target segment, and one success metric."
      }
    ],
    storyArc: [
      `Open with the client decision and why it matters now for ${company}.`,
      "Define the criteria the team used to compare options.",
      "Show the recommendation before diving into supporting analysis.",
      "Defend feasibility with timeline, resources, metrics, and risks.",
      "Close by restating the decision and the next action judges should remember."
    ],
    keywords: keywords.length ? keywords : ["decision criteria", "feasibility", "risk", "metrics", "implementation"],
    difficultQuestions: [
      `What would make you reverse or pause this recommendation for ${company}?`,
      "Which assumption has the highest downside risk, and how would you test it quickly?",
      "How does your recommendation perform against the judging criteria better than the alternatives?",
      "What metric would prove success within the first 30 to 90 days?",
      "If implementation takes longer or costs more than expected, what gets cut first?"
    ]
  };
}

function generateCritique(session, brief) {
  const promptKeywords = extractKeywords(session.casePrompt, 5);
  const recommendationKeywords = extractKeywords(session.teamRecommendation, 5);
  const overlap = promptKeywords.filter((keyword) => recommendationKeywords.includes(keyword));
  const hasNumbers = /\d|%|\$|revenue|cost|margin|roi|profit|budget|cash/i.test(session.teamRecommendation);
  const hasTimeline = /day|week|month|quarter|year|phase|timeline|pilot|roadmap/i.test(session.teamRecommendation);
  const hasRisk = /risk|tradeoff|mitigation|downside|challenge|constraint/i.test(session.teamRecommendation);

  return {
    strengths: [
      overlap.length
        ? `The recommendation reuses case-specific language around ${overlap.slice(0, 3).join(", ")}.`
        : "The team has a draft direction that can be sharpened into a judge-ready recommendation.",
      hasTimeline
        ? "There is at least some implementation timing or sequencing language to build from."
        : "The recommendation is concise enough that a stronger implementation sequence can be added without rebuilding the whole idea.",
      session.slideOutline
        ? "The slide outline gives the team a visible structure for turning critique into presentation edits."
        : "The current recommendation can still be tested quickly before the team invests more time in slide polish."
    ],
    weaknesses: [
      "The answer to the case prompt should be stated in one decisive sentence before analysis details.",
      hasNumbers
        ? "The financial logic is mentioned, but the key assumptions still need a clearer defense."
        : "The financial or operational implication is not yet concrete enough for a judge challenge.",
      hasRisk
        ? "Risks are present, but they should be tied to mitigation triggers and ownership."
        : "The recommendation does not yet acknowledge the highest-risk tradeoff directly."
    ],
    assumptionsToDefend: brief.assumptions,
    missingEvidence: [
      "A baseline metric, target metric, and decision threshold.",
      "A comparison against at least one rejected alternative.",
      "Proof that the target customer or stakeholder is the right first focus."
    ],
    riskAreas: brief.risks.map((item) => item.risk),
    dimensions: [
      {
        name: "Prompt alignment",
        note: overlap.length
          ? "Promising, but make the alignment explicit in the opening."
          : "Needs a clearer bridge between the prompt wording and the recommendation."
      },
      {
        name: "Logic",
        note: "Use a simple chain: objective, criteria, option comparison, recommendation, metric."
      },
      {
        name: "Stakeholder focus",
        note: "Name the target customer, client decision-maker, and operational owner."
      },
      {
        name: "Feasibility",
        note: hasTimeline ? "Add owners and resource needs to the timeline." : "Add timeline, owners, and resource constraints."
      }
    ]
  };
}

function generateQuestions(session, brief, critique) {
  const company = session.companyName || "the client";
  const rubric = parseRubric(session.judgingCriteria);
  const focus = brief.keywords[0] || "the recommendation";

  return [
    {
      id: "q1",
      questionNumber: 1,
      questionText: `In one sentence, what is your recommendation for ${company}, and why does it directly answer the case prompt?`,
      rationale: "Judges often test whether the team can state the decision clearly under pressure.",
      criterionTested: rubric[0] || defaultRubric[0]
    },
    {
      id: "q2",
      questionNumber: 2,
      questionText: `What is the single most important assumption behind your ${focus} logic, and what evidence would you use to defend it?`,
      rationale: "Strong teams separate facts from assumptions and explain how they would validate the riskiest assumption.",
      criterionTested: "Analysis depth and evidence quality"
    },
    {
      id: "q3",
      questionNumber: 3,
      questionText: "What financial or operational metric would tell the client this recommendation is working?",
      rationale: "Judges look for success metrics, not just persuasive language.",
      criterionTested: "Financial or operational reasoning"
    },
    {
      id: "q4",
      questionNumber: 4,
      questionText: `What is the biggest risk or tradeoff in your plan for ${company}, and what would you do if it appears early?`,
      rationale: "Risk answers show whether the team understands downside and contingency planning.",
      criterionTested: "Risk analysis and mitigation"
    },
    {
      id: "q5",
      questionNumber: 5,
      questionText: "If judges only remember one slide or one sentence from your presentation, what should it be?",
      rationale: "A memorable close reveals whether the story arc is coherent.",
      criterionTested: critique.dimensions[0]?.name || "Presentation clarity"
    }
  ];
}

function generateFollowUp(question, answer, session) {
  const answerWords = wordCount(answer);
  const hasNumber = /\d|%|\$|revenue|cost|margin|roi|profit|budget|cash|metric/i.test(answer);
  const hasRisk = /risk|tradeoff|mitigat|downside|challenge|fail|uncertain/i.test(answer);
  const hasTimeline = /day|week|month|quarter|year|phase|timeline|pilot|first|next/i.test(answer);
  const hasRubric = parseRubric(session.judgingCriteria)
    .some((criterion) => {
      const keyword = extractKeywords(criterion, 1)[0];
      return keyword && answer.toLowerCase().includes(keyword);
    });

  if (answerWords < 25) {
    return {
      followUpText: "Can you make that more concrete with one example, metric, or decision threshold?",
      reason: "The answer is short, so a judge may ask for specifics."
    };
  }

  if (!hasNumber && /metric|financial|operational|evidence|assumption/i.test(question.questionText)) {
    return {
      followUpText: "What number, range, or measurable signal would make this answer defensible?",
      reason: "The answer did not include a measurable proof point."
    };
  }

  if (!hasRisk && /risk|tradeoff|assumption/i.test(question.questionText)) {
    return {
      followUpText: "What could go wrong first, and what would your team change if that happened?",
      reason: "The answer needs a clearer downside and mitigation."
    };
  }

  if (!hasTimeline && /implementation|plan|recommendation|working/i.test(question.questionText)) {
    return {
      followUpText: "What is the first milestone and who owns it?",
      reason: "The answer would be stronger with execution timing and accountability."
    };
  }

  if (!hasRubric && session.judgingCriteria.trim()) {
    return {
      followUpText: "Which judging criterion does that response satisfy most directly?",
      reason: "The answer did not explicitly connect to the stated rubric."
    };
  }

  return {
    followUpText: "What is the strongest objection a judge could raise to that answer?",
    reason: "A strong answer should be ready for the next challenge."
  };
}

function deliveryMetrics(answerText, durationSeconds) {
  const words = wordCount(answerText);
  const lower = ` ${answerText.toLowerCase()} `;
  const fillerWordCount = fillerWords.reduce((total, filler) => {
    const pattern = new RegExp(`\\b${filler.replace(" ", "\\s+")}\\b`, "g");
    return total + (lower.match(pattern) || []).length;
  }, 0);
  const approximateWordsPerMinute = durationSeconds > 0 ? Math.round((words / durationSeconds) * 60) : 0;
  return {
    wordCount: words,
    fillerWordCount,
    durationSeconds: Math.max(1, Math.round(durationSeconds || 1)),
    approximateWordsPerMinute
  };
}

function scoreAnswer(answer) {
  const metrics = answer.metrics || deliveryMetrics(answer.answerText, answer.durationSeconds || 60);
  let score = 52;
  const words = metrics.wordCount || wordCount(answer.answerText);
  if (words >= 35) score += 10;
  if (words >= 70) score += 6;
  if (/\d|%|\$|metric|cost|revenue|margin|timeline|pilot|risk/i.test(answer.answerText)) score += 12;
  if (/because|therefore|so that|which means|we chose|we recommend/i.test(answer.answerText)) score += 8;
  if (answer.followUpAnswer && wordCount(answer.followUpAnswer) >= 20) score += 7;
  if (metrics.fillerWordCount > 3) score -= 5;
  if (metrics.approximateWordsPerMinute > 190 || metrics.approximateWordsPerMinute < 85) score -= 4;
  return clamp(score, 35, 96);
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, Math.round(value)));
}

function generateReport(session) {
  const brief = session.caseBrief;
  const critique = session.recommendationCritique;
  const answers = session.answers.slice(0, 5);
  const answerScores = answers.map(scoreAnswer);
  const averageAnswer = answerScores.length
    ? answerScores.reduce((total, score) => total + score, 0) / answerScores.length
    : 55;
  const hasNumbers = /\d|%|\$|revenue|cost|margin|roi|profit|budget|cash/i.test(
    `${session.teamRecommendation} ${answers.map((answer) => answer.answerText).join(" ")}`
  );
  const recommendationStrengthScore = clamp(
    64 +
      (hasNumbers ? 8 : -5) +
      (session.slideOutline ? 5 : 0) +
      (session.teamConstraints ? 4 : 0) -
      Math.max(0, critique.weaknesses.length - 3) * 2,
    40,
    94
  );
  const qnaReadinessScore = clamp(averageAnswer, 35, 96);
  const fillerTotal = answers.reduce((total, answer) => total + (answer.metrics?.fillerWordCount || 0), 0);
  const avgWpm = answers.length
    ? Math.round(
        answers.reduce((total, answer) => total + (answer.metrics?.approximateWordsPerMinute || 0), 0) /
          answers.length
      )
    : 0;
  const presentationClarityScore = clamp(78 - fillerTotal * 2 - (avgWpm > 190 || avgWpm < 85 ? 7 : 0), 40, 95);
  const overallReadinessScore = clamp(
    recommendationStrengthScore * 0.45 + qnaReadinessScore * 0.35 + presentationClarityScore * 0.2,
    35,
    96
  );
  const bestIndex = answerScores.indexOf(Math.max(...answerScores));
  const weakestIndex = answerScores.indexOf(Math.min(...answerScores));
  const missedCriteria = parseRubric(session.judgingCriteria)
    .filter((criterion) => {
      const keywords = extractKeywords(criterion, 2);
      const combined = `${session.teamRecommendation} ${answers.map((answer) => answer.answerText).join(" ")}`.toLowerCase();
      return keywords.length && !keywords.some((keyword) => combined.includes(keyword));
    })
    .slice(0, 4);

  return {
    generatedAt: new Date().toISOString(),
    scores: {
      overallReadinessScore,
      recommendationStrengthScore,
      qnaReadinessScore,
      presentationClarityScore
    },
    strengths: [
      brief.strengths[0],
      "The rehearsal produced answers for all five judge-style prompts.",
      answerScores[bestIndex] >= 70
        ? `The strongest answer gave judges a more defensible response to question ${bestIndex + 1}.`
        : "The team now has a clear list of answer areas to strengthen before presenting."
    ],
    weaknesses: [
      critique.weaknesses[0],
      hasNumbers
        ? "The numerical logic should be tied to a decision threshold, not only mentioned as support."
        : "Missing metrics or numbers remain the clearest judge concern.",
      missedCriteria.length
        ? `Some judging criteria are still under-addressed: ${missedCriteria.join("; ")}.`
        : "Criteria are referenced, but the final story still needs sharper prioritization."
    ],
    missedCriteria: missedCriteria.length ? missedCriteria : ["No major rubric area was fully missing, but scoring links should be made explicit."],
    weakAssumptions: brief.assumptions.slice(0, 3),
    likelyJudgeConcerns: [
      "Why this option is better than the closest alternative.",
      "What metric proves success early.",
      "Which risk could invalidate the recommendation."
    ],
    missingMetricsOrEvidence: [
      "A baseline and target metric.",
      "A timeline or milestone that proves feasibility.",
      "A source, calculation, or labeled assumption for the highest-impact number."
    ],
    bestAnswer: summarizeAnswer(answers[bestIndex], bestIndex),
    weakestAnswer: summarizeAnswer(answers[weakestIndex], weakestIndex),
    improvedAnswers: [
      {
        question: answers[weakestIndex]?.questionText || "Weakest answer",
        suggestion: improvedAnswer(session, answers[weakestIndex])
      }
    ],
    nextPracticePlan: [
      "Rewrite the opening recommendation as one sentence that includes client, action, target, and reason.",
      "Add one measurable success metric and one failure threshold to the financial or operational slide.",
      "Practice the weakest Q&A answer twice: first in 45 seconds, then in 25 seconds.",
      "Ask one teammate to challenge only assumptions and another to challenge only implementation feasibility.",
      "End the deck by repeating the recommendation, the metric, and the next action."
    ],
    deliveryMetrics: {
      totalFillerWords: fillerTotal,
      averageWordsPerMinute: avgWpm,
      note: "Typed-answer timing is approximate. Audio/video delivery claims are not inferred."
    }
  };
}

function summarizeAnswer(answer, index) {
  if (!answer) {
    return {
      questionNumber: 0,
      summary: "No answer recorded."
    };
  }
  return {
    questionNumber: index + 1,
    question: answer.questionText,
    summary: compactSentence(answer.answerText, "Answer recorded."),
    score: scoreAnswer(answer)
  };
}

function improvedAnswer(session, answer) {
  const company = session.companyName || "the client";
  const metric = session.caseBrief?.keywords?.[0] || "success metric";
  const question = answer?.questionText || "the judge question";
  return `A stronger response to "${question}" would start with the direct answer, then give evidence and a caveat: "For ${company}, our recommendation is strongest if it improves ${metric} without exceeding the stated constraints. The assumption we would defend is the adoption or execution rate. We would test it with a first milestone, compare it against our base case, and pause expansion if the metric misses the threshold."`;
}

function render() {
  const route = routeFromHash();

  if (route === "setup") renderSetup();
  else if (route === "brief") renderBrief();
  else if (route === "rehearsal") renderRehearsal();
  else if (route === "report") renderReport();
  else renderHome();
  bindChromeActions();
  app.focus({ preventScroll: true });
}

function loadingMarkup(label) {
  return `<span class="loading"><span class="spinner"></span>${escapeHtml(label)}</span>`;
}

function initials(name) {
  return String(name || "CM")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("") || "CM";
}

function topNavMarkup(step = 0) {
  const progress = [
    { route: "setup", label: "Setup" },
    { route: "brief", label: "Brief" },
    { route: "rehearsal", label: "Q&A" },
    { route: "report", label: "Report" }
  ];

  const homeLinks = `
    <nav class="cm-home-links" aria-label="Main">
      <a href="#/">Home</a>
      <a href="#/setup">Method</a>
      <a href="#/report">Sample report</a>
      <a href="#/rehearsal">For teams</a>
    </nav>
  `;

  const stepLinks = `
    <div class="cm-step-links" aria-label="Progress">
      ${progress
        .map((item, index) => {
          const itemStep = index + 1;
          const stateClass = itemStep < step ? "done" : itemStep === step ? "active" : "";
          return `
            <a class="cm-step-link ${stateClass}" href="#/${item.route}">
              <span class="cm-step-dot">${itemStep < step ? "✓" : itemStep}</span>
              <span>${item.label}</span>
            </a>
          `;
        })
        .join('<span class="cm-step-divider"></span>')}
    </div>
  `;

  return `
    <header class="cm-topbar">
      <a class="cm-brand" href="#/">
        <span class="cm-brand-mark">
          <svg viewBox="0 0 28 28" aria-hidden="true">
            <rect x="1.5" y="1.5" width="25" height="25" rx="6"></rect>
            <path d="M8 14 L13 19 L20 9"></path>
          </svg>
        </span>
        <span class="cm-brand-copy">
          <strong>Case Mirror</strong>
          <small>Competition prep</small>
        </span>
      </a>

      ${step === 0 ? homeLinks : stepLinks}

      <div class="cm-topbar-actions">
        ${step === 0 ? '<a class="cm-link-btn" href="#/report">Preview report</a>' : `<span class="cm-session-chip">session · ${escapeHtml(initials(state.session.companyName || "CM"))}-${state.session.id.slice(0, 4)}</span>`}
        <button class="cm-pill-btn cm-pill-btn--ghost" id="clearSessionBtn" type="button">Clear session</button>
        ${step === 0 ? '<a class="cm-pill-btn cm-pill-btn--teal" href="#/setup">Start session</a>' : '<a class="cm-pill-btn cm-pill-btn--navy" href="#/">Home</a>'}
      </div>
    </header>
  `;
}

function shellMarkup(step, bodyMarkup, extraClass = "") {
  return `
    <section class="cm-page ${extraClass}">
      ${topNavMarkup(step)}
      ${bodyMarkup}
    </section>
  `;
}

function scoreLabel(value) {
  if (value >= 80) return "Clear";
  if (value >= 68) return "Steady";
  if (value >= 55) return "Watch";
  return "Thin";
}

function scoreTone(value) {
  if (value >= 80) return "good";
  if (value >= 68) return "good";
  if (value >= 55) return "warn";
  return "warn";
}

function bindChromeActions() {
  document.getElementById("clearSessionBtn")?.addEventListener("click", clearSession);
}

function renderHome() {
  app.innerHTML = shellMarkup(
    0,
    `
      <section class="cm-hero">
        <div class="cm-hero-media">
          <div class="cm-orb cm-orb--teal"></div>
          <div class="cm-orb cm-orb--blue"></div>
          <div class="cm-media-card">
            <div class="cm-live-chip">Live brief</div>
            <div class="cm-placeholder cm-placeholder--blue" aria-label="Case brief preview">
              <span>[ Case brief preview ]</span>
              <small>Generated brief on a desk / over-the-shoulder team prep</small>
            </div>
            <div class="cm-floating-metric">
              <div class="cm-metric-head">
                <span>Readiness</span>
                <strong>68.5%</strong>
              </div>
              <div class="cm-sparkbars">
                <span style="height: 14px"></span>
                <span style="height: 22px"></span>
                <span style="height: 18px"></span>
                <span style="height: 28px"></span>
                <span style="height: 25px"></span>
                <span style="height: 32px" class="accent"></span>
                <span style="height: 27px" class="accent-dark"></span>
                <span style="height: 30px" class="accent"></span>
              </div>
              <p>Across 5 typed answers · practice feedback only</p>
            </div>
          </div>
        </div>

        <div class="cm-hero-copy">
          <span class="cm-badge cm-badge--teal">AI rehearsal</span>
          <h1>Case-<span>Ready.</span><br />Question-Ready.</h1>
          <p>
            Practice for the exact case competition you're about to present.
            Paste the prompt, run a judge Q&amp;A, and get a written readiness
            report with strengths, risks, and the answers you still owe.
          </p>
          <div class="cm-hero-actions">
            <button class="primary-btn cm-button-lift" id="startBtn" type="button">Start a session</button>
            <button class="secondary-btn cm-video-btn" id="sampleBtn" type="button">
              Load sample case
              <span>▶</span>
            </button>
          </div>
          <div class="cm-rating">
            <div class="cm-stars"><strong>4.9</strong><span>★★★★★</span></div>
            <div class="cm-avatars">
              <span>CK</span><span>MO</span><span>RA</span><span>+11</span>
            </div>
            <p>Case teams at 14 universities rehearse with Case Mirror before competition weekends.</p>
          </div>
        </div>
      </section>

      <section class="cm-section">
        <div class="cm-section-head">
          <div>
            <span class="cm-badge cm-badge--blue">Method</span>
            <h2>Built for the case<br />you're about to present.</h2>
          </div>
          <div class="cm-section-copy">
            <span class="cm-eyebrow">How it works</span>
            <p>Three steps. One written readiness report at the end. Run the loop before the panel and the answers stop being improvised.</p>
          </div>
        </div>

        <div class="cm-feature-grid">
          <article class="cm-feature-card">
            <span class="cm-badge cm-badge--teal">Generated</span>
            <h3>Parallel Brief</h3>
            <p>A brief shaped like the case room: situation, core decision, likely pressure points, and defensible questions.</p>
            <div class="cm-placeholder cm-placeholder--soft"><span>[ Brief mock ]</span></div>
            <div class="cm-card-foot"><span>01 / 03</span><a href="#/brief">See example</a></div>
          </article>

          <article class="cm-feature-card cm-feature-card--focus">
            <div class="cm-card-top">
              <span class="cm-badge cm-badge--lavender">Rehearsal</span>
              <div class="cm-arrow-pair"><span>←</span><span>→</span></div>
            </div>
            <h3>Judge Q&amp;A</h3>
            <p>Typed answers first. Mic and camera are optional, never required. The panel voice stays grounded in the case you pasted.</p>
            <div class="cm-placeholder cm-placeholder--lavender">
              <span>[ Q&amp;A transcript ]</span>
              <small>Judge prompt + your answer + practice note</small>
            </div>
            <a class="cm-blue-link" href="#/rehearsal">See sample Q&amp;A <span>↗</span></a>
          </article>

          <article class="cm-feature-card">
            <span class="cm-badge cm-badge--green">Output</span>
            <h3>Readiness Report</h3>
            <p>Strengths, risks, and the answers you still owe. Written feedback, not official judging and not winner prediction.</p>
            <div class="cm-placeholder cm-placeholder--green"><span>[ Report mock ]</span></div>
            <div class="cm-card-foot"><span>03 / 03</span><a href="#/report">Sample report</a></div>
          </article>
        </div>
      </section>

      <section class="cm-section cm-team-grid">
        <div class="cm-team-copy">
          <span class="cm-badge cm-badge--teal">For teams</span>
          <h2>Rehearsing the<br />case competition.</h2>
          <p>
            We help university case teams walk into the room having already
            practiced the questions they will face — calmly, in writing, before
            the panel opens its mouth.
          </p>
          <ul class="cm-check-list">
            <li>Prompt-aligned practice</li>
            <li>Typed-answer first</li>
            <li>Written readiness report</li>
          </ul>
        </div>

        <div class="cm-team-panels">
          <div class="cm-stat-stack">
            <article class="cm-stat-card cm-stat-card--teal"><strong>1,800+</strong><span>rehearsals run</span></article>
            <article class="cm-stat-card cm-stat-card--blue"><strong>5</strong><span>judge questions per run</span></article>
            <article class="cm-stat-card cm-stat-card--green"><strong>0</strong><span>body-language scoring</span></article>
          </div>
          <article class="cm-dark-panel">
            <div class="cm-placeholder cm-placeholder--dark">
              <span>[ Team rehearsal image ]</span>
              <small>Presentation practice in front of a panel</small>
            </div>
            <div class="cm-dark-panel-copy">
              <strong>Practice feedback only</strong>
              <p>No emotion analysis, no personality scoring, no winner prediction, no official judging.</p>
            </div>
          </article>
        </div>
      </section>
    `,
    "cm-home"
  );

  document.getElementById("startBtn").addEventListener("click", () => go("setup"));
  document.getElementById("sampleBtn").addEventListener("click", () => {
    state.session = { ...createSession(), ...sampleInput };
    saveSession();
    showToast("Sample case loaded.");
    go("setup");
  });
}

function renderSetup() {
  const session = state.session;
  app.innerHTML = shellMarkup(
    1,
    `
      <section class="cm-section cm-setup-head">
        <div>
          <span class="cm-badge cm-badge--teal">Step 1 · Setup</span>
          <h1 class="cm-page-title">Set up your <span>rehearsal.</span></h1>
          <p class="cm-page-lead">Paste the materials your team is already using. Judging criteria are recommended, but the app still works with a general rubric if you leave them blank.</p>
        </div>
        <button class="secondary-btn" id="loadSampleSetupBtn" type="button">Load sample</button>
      </section>

      <section class="cm-form-layout">
        <form class="cm-card cm-form-card" id="setupForm">
          ${state.error ? `<div class="cm-alert cm-alert--danger">${escapeHtml(state.error)}</div>` : ""}

          <div class="cm-form-section">
            <div class="cm-form-label">
              <span>01</span>
              <div>
                <h3>The case prompt</h3>
                <p>Paste the exact prompt your team received. The closer to verbatim, the closer the rehearsal.</p>
              </div>
            </div>
            <label class="cm-field full">
              <span>Case prompt <em>*</em></span>
              <textarea class="large" id="casePrompt" data-field="casePrompt" placeholder="Paste the full case prompt, client objective, constraints, and required deliverable.">${escapeHtml(session.casePrompt)}</textarea>
              ${state.setupErrors.casePrompt ? `<small class="error-text">${state.setupErrors.casePrompt}</small>` : ""}
            </label>
          </div>

          <div class="cm-form-divider"></div>

          <div class="cm-form-section">
            <div class="cm-form-label">
              <span>02</span>
              <div>
                <h3>Your current recommendation</h3>
                <p>Paste the draft recommendation, slide notes, or rough solution your team wants to defend.</p>
              </div>
            </div>
            <label class="cm-field full">
              <span>Team recommendation <em>*</em></span>
              <textarea class="large" id="teamRecommendation" data-field="teamRecommendation" placeholder="Paste your current recommendation, rough solution, slide notes, or strategic direction.">${escapeHtml(session.teamRecommendation)}</textarea>
              ${state.setupErrors.teamRecommendation ? `<small class="error-text">${state.setupErrors.teamRecommendation}</small>` : ""}
            </label>
          </div>

          <div class="cm-form-divider"></div>

          <div class="cm-form-section">
            <div class="cm-form-label">
              <span>03</span>
              <div>
                <h3>Rubric and case context</h3>
                <p>Give the judges' lens and any context that would change how the panel presses your answers.</p>
              </div>
            </div>
            <div class="cm-field-grid">
              <label class="cm-field full">
                <span>Judging criteria or rubric</span>
                <textarea id="judgingCriteria" data-field="judgingCriteria" placeholder="Paste the official rubric if you have it.">${escapeHtml(session.judgingCriteria)}</textarea>
                <small class="hint">Recommended but not required.</small>
              </label>
              <label class="cm-field">
                <span>Company or organization</span>
                <input id="companyName" data-field="companyName" value="${escapeHtml(session.companyName)}" placeholder="Example: EcoRide" />
              </label>
              <label class="cm-field">
                <span>Target presentation length</span>
                <input id="targetPresentationLength" data-field="targetPresentationLength" value="${escapeHtml(session.targetPresentationLength)}" placeholder="Example: 10 minutes" />
              </label>
              <label class="cm-field full">
                <span>Industry context</span>
                <textarea id="industryContext" data-field="industryContext" placeholder="Optional company, market, competitor, or industry notes.">${escapeHtml(session.industryContext)}</textarea>
              </label>
              <label class="cm-field full">
                <span>Team constraints</span>
                <textarea id="teamConstraints" data-field="teamConstraints" placeholder="Optional time, budget, data, implementation, or team constraints.">${escapeHtml(session.teamConstraints)}</textarea>
              </label>
              <label class="cm-field full">
                <span>Slide outline or speaking notes</span>
                <textarea id="slideOutline" data-field="slideOutline" placeholder="Optional slide outline, speaking notes, or current deck structure.">${escapeHtml(session.slideOutline)}</textarea>
              </label>
            </div>
          </div>

          <div class="cm-form-actions">
            <div class="cm-form-status">Nothing is submitted to your real judges. Practice feedback only.</div>
            <div class="cm-form-action-group">
              ${state.loading === "brief" ? loadingMarkup("Building a targeted prep brief") : ""}
              <button class="primary-btn cm-button-lift" type="submit" ${state.loading ? "disabled" : ""}>${state.loading === "brief" ? "Generating..." : "Generate brief"}</button>
            </div>
          </div>
        </form>

        <aside class="cm-sidebar">
          <section class="cm-card">
            <span class="cm-eyebrow">What you'll get</span>
            <h3>A parallel brief, written Q&amp;A, and a readiness report.</h3>
            <ul class="cm-aside-list">
              <li><strong>01 · Case brief</strong><span>Problem summary, key decision, story arc, likely judge questions.</span></li>
              <li><strong>02 · Judge Q&amp;A</strong><span>Five prompts plus adaptive follow-ups in the competition's voice.</span></li>
              <li><strong>03 · Final report</strong><span>Strengths, risks, practice priorities, and answer-level notes.</span></li>
            </ul>
          </section>

          <section class="cm-card">
            <div class="cm-placeholder cm-placeholder--teal cm-placeholder--short">
              <span>[ Live brief preview ]</span>
              <small>Updates as you fill the form</small>
            </div>
            <div class="cm-note-stack">
              <strong>Academic integrity note</strong>
              <p>Use this for critique and rehearsal. Do not fabricate facts, bypass competition rules, or replace original team thinking.</p>
            </div>
          </section>
        </aside>
      </section>
    `,
    "cm-setup"
  );

  document.querySelectorAll("[data-field]").forEach((field) => {
    field.addEventListener("input", () => {
      state.session[field.dataset.field] = field.value;
      saveSession();
    });
  });

  document.getElementById("loadSampleSetupBtn").addEventListener("click", () => {
    state.session = { ...createSession(), ...sampleInput };
    state.setupErrors = {};
    saveSession();
    showToast("Sample case loaded.");
    render();
  });

  document.getElementById("setupForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    persistSetupForm();
    state.setupErrors = {};

    if (!state.session.casePrompt.trim()) {
      state.setupErrors.casePrompt = "Case prompt is required.";
    }
    if (!state.session.teamRecommendation.trim()) {
      state.setupErrors.teamRecommendation = "Team recommendation is required.";
    }
    if (Object.keys(state.setupErrors).length) {
      render();
      return;
    }

    await withLoading("brief", async () => {
      const brief = generateBrief(state.session);
      const critique = generateCritique(state.session, brief);
      const questions = generateQuestions(state.session, brief, critique);
      state.session.caseBrief = brief;
      state.session.recommendationCritique = critique;
      state.session.questions = questions;
      state.session.answers = [];
      state.session.finalReport = null;
      state.session.timerStartedAt = null;
      saveSession();
      go("brief");
    });
  });
}

function persistSetupForm() {
  document.querySelectorAll("[data-field]").forEach((field) => {
    state.session[field.dataset.field] = field.value.trim();
  });
  saveSession();
}

function ensureBrief() {
  return state.session.caseBrief && state.session.recommendationCritique && state.session.questions.length === 5;
}

function renderBrief() {
  if (!ensureBrief()) {
    renderEmpty("Generate a case brief first", "Paste your case materials so Case Mirror can build a targeted prep brief.", "Go to setup", "setup");
    return;
  }

  const brief = state.session.caseBrief;
  const critique = state.session.recommendationCritique;
  app.innerHTML = shellMarkup(
    2,
    `
      <section class="cm-section cm-brief-head">
        <div>
          <span class="cm-badge cm-badge--blue">Step 2 · Brief</span>
          <h1 class="cm-page-title">Pressure-test the <span>recommendation.</span></h1>
          <p class="cm-page-lead">Use this as the written version of what the panel is about to ask you to defend.</p>
        </div>
        <div class="cm-head-actions">
          <button class="secondary-btn" id="editInputsBtn" type="button">Edit inputs</button>
          <button class="primary-btn cm-button-lift" id="startRehearsalBtn" type="button">Start Q&amp;A</button>
        </div>
      </section>

      <section class="cm-doc-layout">
        <article class="cm-doc-card">
          ${brief.usesDefaultRubric ? `<div class="cm-alert cm-alert--soft"><strong>General rubric used.</strong><span>No judging criteria were provided, so this brief uses a general case competition rubric.</span></div>` : ""}
          <div class="cm-doc-section">
            <span class="cm-doc-kicker">Situation</span>
            <h2>Problem summary</h2>
            <p>${escapeHtml(brief.problemSummary)}</p>
          </div>
          <div class="cm-doc-section">
            <span class="cm-doc-kicker">Decision</span>
            <h2>Key decision required</h2>
            <p>${escapeHtml(brief.keyDecision)}</p>
          </div>
          <div class="cm-doc-grid">
            <section class="cm-doc-section">
              <span class="cm-doc-kicker">Story arc</span>
              <h3>Suggested sequence</h3>
              ${listMarkup(brief.storyArc)}
            </section>
            <section class="cm-doc-section">
              <span class="cm-doc-kicker">Pressure points</span>
              <h3>Likely difficult questions</h3>
              ${listMarkup(brief.difficultQuestions, "warning")}
            </section>
          </div>
          <div class="cm-doc-grid">
            <section class="cm-doc-section">
              <span class="cm-doc-kicker">Criteria</span>
              <h3>Likely judge priorities</h3>
              ${listMarkup(brief.judgePriorities)}
            </section>
            <section class="cm-doc-section">
              <span class="cm-doc-kicker">Signals</span>
              <h3>Keywords to emphasize</h3>
              <div class="cm-tag-row">${brief.keywords.map((item) => `<span class="cm-tag">${escapeHtml(item)}</span>`).join("")}</div>
            </section>
          </div>
          <div class="cm-doc-grid">
            <section class="cm-doc-section">
              <span class="cm-doc-kicker">What holds</span>
              <h3>Strengths</h3>
              ${listMarkup(brief.strengths)}
            </section>
            <section class="cm-doc-section">
              <span class="cm-doc-kicker">What breaks</span>
              <h3>Gaps</h3>
              ${listMarkup(brief.gaps, "warning")}
            </section>
          </div>
          <div class="cm-doc-section">
            <span class="cm-doc-kicker">Assumptions</span>
            <h3>Assumptions to defend</h3>
            ${listMarkup(brief.assumptions)}
          </div>
          <div class="cm-doc-section">
            <span class="cm-doc-kicker">Mitigation</span>
            <h3>Risks and mitigation ideas</h3>
            <div class="cm-mini-grid">
              ${brief.risks
                .map(
                  (item) => `
                    <div class="cm-mini-card">
                      <strong>${escapeHtml(item.risk)}</strong>
                      <p>${escapeHtml(item.mitigation)}</p>
                    </div>
                  `
                )
                .join("")}
            </div>
          </div>
        </article>

        <aside class="cm-sidebar">
          <section class="cm-card">
            <span class="cm-eyebrow">Session meta</span>
            <div class="cm-stat-row">
              <div><span>Questions</span><strong>5</strong></div>
              <div><span>Keywords</span><strong>${brief.keywords.length}</strong></div>
              <div><span>Risks</span><strong>${brief.risks.length}</strong></div>
              <div><span>Rubric</span><strong>${brief.usesDefaultRubric ? "General" : "Custom"}</strong></div>
            </div>
          </section>

          <section class="cm-card">
            <span class="cm-eyebrow">Recommendation critique</span>
            <div class="cm-critique-block">
              <h3>Strengths</h3>
              ${listMarkup(critique.strengths)}
            </div>
            <div class="cm-critique-block">
              <h3>Improvement areas</h3>
              ${listMarkup(critique.weaknesses, "warning")}
            </div>
            <div class="cm-critique-block">
              <h3>Missing evidence</h3>
              ${listMarkup(critique.missingEvidence, "coral")}
            </div>
          </section>
        </aside>
      </section>
    `,
    "cm-brief"
  );

  document.getElementById("editInputsBtn").addEventListener("click", () => go("setup"));
  document.getElementById("startRehearsalBtn").addEventListener("click", () => {
    if (!state.session.timerStartedAt) {
      state.session.timerStartedAt = Date.now();
      saveSession();
    }
    go("rehearsal");
  });
}

function listMarkup(items, style = "") {
  return `<ul class="mini-list ${style}">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function renderEmpty(title, body, button, route) {
  app.innerHTML = shellMarkup(
    route === "setup" ? 1 : route === "brief" ? 2 : route === "rehearsal" ? 3 : 4,
    `
      <section class="cm-empty">
        <div class="cm-card cm-empty-card">
          <span class="cm-badge cm-badge--amber">Action needed</span>
          <h1 class="cm-page-title">${escapeHtml(title)}</h1>
          <p class="cm-page-lead">${escapeHtml(body)}</p>
          <button class="primary-btn cm-button-lift" id="emptyActionBtn" type="button">${escapeHtml(button)}</button>
        </div>
      </section>
    `
  );
  document.getElementById("emptyActionBtn").addEventListener("click", () => go(route));
}

function currentRehearsalState() {
  const answers = state.session.answers || [];
  if (!answers.length) return { index: 0, phase: "main" };
  const last = answers[answers.length - 1];
  if (!last.followUpAnswer) return { index: answers.length - 1, phase: "followup" };
  return { index: answers.length, phase: "main" };
}

function renderRehearsal() {
  if (!ensureBrief()) {
    renderEmpty("Generate a case brief first", "The rehearsal questions are created from the case brief and critique.", "Go to setup", "setup");
    return;
  }

  const session = state.session;
  const progress = currentRehearsalState();

  if (progress.index >= 5) {
    app.innerHTML = shellMarkup(
      3,
      `
        <section class="cm-section cm-qa-complete">
          <div>
            <span class="cm-badge cm-badge--green">Step 3 · Rehearsal complete</span>
            <h1 class="cm-page-title">Five answers down. Build the <span>report.</span></h1>
            <p class="cm-page-lead">All five main judge-style questions have answers and adaptive follow-ups recorded.</p>
          </div>
          <button class="primary-btn cm-button-lift" id="generateReportBtn" type="button">${state.loading === "report" ? "Generating..." : "Generate final report"}</button>
        </section>
        <section class="cm-card">
          <h3 class="cm-card-title">Answer transcript</h3>
          <div class="cm-answer-stack">${session.answers.map(answerTranscriptMarkup).join("")}</div>
        </section>
      `,
      "cm-rehearsal"
    );
    document.getElementById("generateReportBtn").addEventListener("click", () => createReport());
    return;
  }

  const question = session.questions[progress.index];
  if (!session.timerStartedAt || progress.phase === "main") {
    session.timerStartedAt = Date.now();
    saveSession();
  }

  const answer = session.answers[progress.index];
  const isFollowUp = progress.phase === "followup";
  const prompt = isFollowUp ? answer.followUp.followUpText : question.questionText;
  const helper = isFollowUp
    ? `Follow-up reason: ${answer.followUp.reason}`
    : `${question.rationale} Criterion tested: ${question.criterionTested}.`;
  const progressPercent = Math.round((progress.index / 5) * 100);

  app.innerHTML = shellMarkup(
    3,
    `
      <section class="cm-section cm-qa-head">
        <div>
          <span class="cm-badge cm-badge--lavender">Step 3 · Judge Q&amp;A</span>
          <h1 class="cm-page-title">Rehearse the <span>panel.</span></h1>
          <p class="cm-page-lead">Typed answers are the primary path. Microphone transcription and webcam preview are optional add-ons.</p>
        </div>
        <button class="secondary-btn" id="backToBriefBtn" type="button">Back to brief</button>
      </section>

      <section class="cm-qa-layout">
        <article class="cm-card cm-qa-card">
          <div class="cm-qa-progress">
            <div class="cm-progress-label">
              <strong>Question ${progress.index + 1} of 5</strong>
              <span>${isFollowUp ? "Follow-up" : "Main question"}</span>
            </div>
            <div class="cm-progress-dots">
              ${Array.from({ length: 5 }, (_, index) => `<span class="${index < progress.index ? "done" : index === progress.index ? "active" : ""}"></span>`).join("")}
            </div>
            <div class="progress-rail"><span style="width: ${progressPercent}%"></span></div>
          </div>

          <div class="cm-question-panel">
            <span class="cm-eyebrow">${isFollowUp ? "Follow-up prompt" : "Judge prompt"}</span>
            <div class="question-text">${escapeHtml(prompt)}</div>
            <p class="rationale">${escapeHtml(helper)}</p>
          </div>

          <label class="cm-field full">
            <span>${isFollowUp ? "Follow-up answer" : "Your answer"}</span>
            <textarea class="large" id="answerText" placeholder="Type your answer here. Aim for answer first, evidence second, caveat third."></textarea>
            <small class="hint" id="liveMetrics">Words: 0 | Filler words: 0 | Timing starts when the question appears.</small>
          </label>

          <div class="cm-form-actions">
            <div class="cm-form-status">Practice feedback only. No emotion analysis, no body-language scoring, no official judging.</div>
            <div class="cm-form-action-group">
              <button class="secondary-btn" id="micBtn" type="button">Use microphone</button>
              <button class="primary-btn cm-button-lift" id="saveAnswerBtn" type="button">${isFollowUp ? "Save follow-up" : "Save answer and get follow-up"}</button>
            </div>
          </div>
        </article>

        <aside class="cm-sidebar">
          <section class="cm-card cm-webcam-card">
            <span class="cm-eyebrow">Optional preview</span>
            <h3>Camera and self-review</h3>
            <video id="webcamPreview" autoplay muted playsinline></video>
            <button class="secondary-btn" id="webcamBtn" type="button">Enable preview</button>
            <p>Preview only. This MVP does not record video, infer emotion, assess personality, or judge protected traits.</p>
          </section>

          <section class="cm-card">
            <span class="cm-eyebrow">Completed answers</span>
            ${
              session.answers.length
                ? `<div class="cm-answer-stack">${session.answers.map(answerTranscriptMarkup).join("")}</div>`
                : `<p class="cm-muted-copy">Your transcripts will appear here as you practice.</p>`
            }
          </section>
        </aside>
      </section>
    `,
    "cm-rehearsal"
  );

  document.getElementById("backToBriefBtn").addEventListener("click", () => go("brief"));
  document.getElementById("answerText").addEventListener("input", updateLiveMetrics);
  document.getElementById("saveAnswerBtn").addEventListener("click", () => saveRehearsalAnswer(progress, question));
  document.getElementById("micBtn").addEventListener("click", toggleMic);
  document.getElementById("webcamBtn").addEventListener("click", enableWebcam);
  updateLiveMetrics();
}

function answerTranscriptMarkup(answer) {
  return `
    <div class="cm-answer-card">
      <h3>Q${answer.questionNumber}: ${escapeHtml(answer.questionText)}</h3>
      <p>${escapeHtml(compactSentence(answer.answerText, "No main answer recorded."))}</p>
      ${
        answer.followUp
          ? `<p class="hint"><strong>Follow-up:</strong> ${escapeHtml(answer.followUp.followUpText)}</p>
             <p>${escapeHtml(compactSentence(answer.followUpAnswer || "", "Follow-up not answered yet."))}</p>`
          : ""
      }
      ${
        answer.metrics
          ? `<div class="cm-answer-metrics">
              <div><strong>${answer.metrics.wordCount}</strong><span>words</span></div>
              <div><strong>${answer.metrics.fillerWordCount}</strong><span>fillers</span></div>
              <div><strong>${answer.metrics.durationSeconds}s</strong><span>duration</span></div>
              <div><strong>${answer.metrics.approximateWordsPerMinute}</strong><span>wpm</span></div>
            </div>`
          : ""
      }
    </div>
  `;
}

function updateLiveMetrics() {
  const text = document.getElementById("answerText")?.value || "";
  const started = state.session.timerStartedAt || Date.now();
  const elapsed = Math.max(1, Math.round((Date.now() - started) / 1000));
  const metrics = deliveryMetrics(text, elapsed);
  const live = document.getElementById("liveMetrics");
  if (live) {
    live.textContent = `Words: ${metrics.wordCount} | Filler words: ${metrics.fillerWordCount} | Approx pace: ${metrics.approximateWordsPerMinute} WPM | Elapsed: ${elapsed}s`;
  }
}

function saveRehearsalAnswer(progress, question) {
  const answerText = textValue("answerText");
  if (!answerText) {
    showToast("Add an answer before saving.");
    return;
  }

  const elapsed = Math.max(1, Math.round((Date.now() - (state.session.timerStartedAt || Date.now())) / 1000));

  if (progress.phase === "followup") {
    state.session.answers[progress.index].followUpAnswer = answerText;
    state.session.answers[progress.index].followUpMetrics = deliveryMetrics(answerText, elapsed);
    state.session.timerStartedAt = Date.now();
    saveSession();
    render();
    return;
  }

  const followUp = generateFollowUp(question, answerText, state.session);
  const metrics = deliveryMetrics(answerText, elapsed);
  state.session.answers[progress.index] = {
    id: createId(),
    questionId: question.id,
    questionNumber: question.questionNumber,
    questionText: question.questionText,
    rationale: question.rationale,
    criterionTested: question.criterionTested,
    answerText,
    inputMode: state.micActive ? "microphone_transcription" : "typed",
    durationSeconds: elapsed,
    metrics,
    followUp,
    followUpAnswer: ""
  };
  state.session.timerStartedAt = Date.now();
  saveSession();
  render();
}

function toggleMic() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    showToast("Microphone transcription is not available in this browser. Typed answers still work.");
    return;
  }

  if (state.recognition && state.micActive) {
    state.recognition.stop();
    state.micActive = false;
    showToast("Microphone stopped.");
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = "en-US";
  recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
      .map((result) => result[0].transcript)
      .join(" ");
    const textarea = document.getElementById("answerText");
    if (textarea) {
      textarea.value = transcript;
      updateLiveMetrics();
    }
  };
  recognition.onerror = () => {
    state.micActive = false;
    showToast("Microphone transcription failed. Typed answers still work.");
  };
  recognition.onend = () => {
    state.micActive = false;
  };
  state.recognition = recognition;
  state.micActive = true;
  recognition.start();
  showToast("Microphone transcription started.");
}

async function enableWebcam() {
  const video = document.getElementById("webcamPreview");
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showToast("Webcam preview is not available in this browser.");
    return;
  }
  try {
    if (!state.webcamStream) {
      state.webcamStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    }
    video.srcObject = state.webcamStream;
    showToast("Webcam preview enabled.");
  } catch (error) {
    showToast("Webcam permission was blocked or unavailable. Rehearsal still works with typed answers.");
  }
}

async function createReport() {
  if ((state.session.answers || []).filter((answer) => answer.followUpAnswer).length < 5) {
    showToast("Complete all five questions and follow-ups first.");
    return;
  }
  await withLoading("report", async () => {
    state.session.finalReport = generateReport(state.session);
    saveSession();
    go("report");
  });
}

function renderReport() {
  if (!ensureBrief()) {
    renderEmpty("Generate a case brief first", "The final report needs a brief and rehearsal transcript.", "Go to setup", "setup");
    return;
  }

  if (!state.session.finalReport && (state.session.answers || []).filter((answer) => answer.followUpAnswer).length >= 5) {
    state.session.finalReport = generateReport(state.session);
    saveSession();
  }

  if (!state.session.finalReport) {
    renderEmpty("Complete rehearsal first", "Answer all five judge-style questions and follow-ups before creating the readiness report.", "Go to Q&A", "rehearsal");
    return;
  }

  const report = state.session.finalReport;
  const scores = report.scores;
  app.innerHTML = shellMarkup(
    4,
    `
      <section class="cm-report-hero">
        <div class="cm-report-cover">
          <div class="cm-report-cover-top">
            <div>
              <span class="cm-badge cm-badge--glass">Step 4 · Readiness report</span>
              <span class="cm-report-session">Session ${escapeHtml(initials(state.session.companyName || "CM"))}-${state.session.id.slice(0, 4)}</span>
            </div>
            <div class="cm-report-actions">
              <button class="secondary-btn" id="copyReportBtn" type="button">Copy report</button>
              <button class="secondary-btn" id="exportReportBtn" type="button">Export JSON</button>
              <button class="primary-btn cm-button-lift" id="restartBtn" type="button">Restart with same inputs</button>
            </div>
          </div>

          <div class="cm-report-cover-grid">
            <div>
              <span class="cm-report-kicker">${escapeHtml(state.session.companyName || "Untitled case")} · practice transcript</span>
              <h1>You're <em>almost</em> ready for the panel.</h1>
              <p>
                Five of your answers held up well enough to rehearse live.
                The recommendation is structurally stronger than the weaker
                evidence points. Use this report as practice guidance only,
                not official judging.
              </p>
              <div class="cm-report-chip-row">
                <span>Recommendation defensible</span>
                <span>Q&amp;A transcript complete</span>
                <span>No winner prediction</span>
              </div>
            </div>

            <div class="cm-report-meta">
              <div class="cm-report-meta-card">
                <div><span>Overall</span><strong>${scores.overallReadinessScore}</strong></div>
                <div><span>Q&amp;A</span><strong>${scores.qnaReadinessScore}</strong></div>
                <div><span>Clarity</span><strong>${scores.presentationClarityScore}</strong></div>
                <div><span>Answers</span><strong>${state.session.answers.length}/5</strong></div>
              </div>
              <div class="cm-report-pillar-row">
                <article><span>Strengths</span><strong>${report.strengths.length}</strong></article>
                <article><span>Risks</span><strong>${report.weaknesses.length}</strong></article>
                <article><span>Next reps</span><strong>${report.nextPracticePlan.length}</strong></article>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="cm-section">
        <div class="cm-section-head">
          <div>
            <span class="cm-eyebrow">How you read by area</span>
            <h2>Where you're solid, where the panel will lean in.</h2>
          </div>
          <p class="cm-section-note">Categorical reads only. We don't predict rankings, confidence, personality, or competition outcomes.</p>
        </div>
        <div class="cm-score-grid">
          ${[
            ["Overall readiness", scores.overallReadinessScore],
            ["Recommendation strength", scores.recommendationStrengthScore],
            ["Judge Q&A readiness", scores.qnaReadinessScore],
            ["Presentation clarity", scores.presentationClarityScore]
          ]
            .map(
              ([label, value]) => `
                <article class="cm-score-card">
                  <div class="cm-score-head">
                    <span>${label}</span>
                    <strong>${scoreLabel(value)}</strong>
                  </div>
                  <div class="cm-score-value">${value}<small>/100</small></div>
                  <div class="cm-score-track ${scoreTone(value)}"><span style="width: ${value}%"></span></div>
                </article>
              `
            )
            .join("")}
        </div>
      </section>

      <section class="cm-section cm-report-columns">
        <article class="cm-card">
          <span class="cm-eyebrow">Strengths</span>
          <h3>Where the panel won't press</h3>
          ${listMarkup(report.strengths)}
        </article>
        <article class="cm-card">
          <span class="cm-eyebrow">Risks</span>
          <h3>Where they will press</h3>
          ${listMarkup(report.weaknesses, "warning")}
        </article>
        <article class="cm-card">
          <span class="cm-eyebrow">Next reps</span>
          <h3>What to rehearse next</h3>
          ${listMarkup(report.nextPracticePlan)}
        </article>
      </section>

      <section class="cm-section">
        <div class="cm-report-detail-grid">
          <article class="cm-card">
            <span class="cm-eyebrow">Criteria to shore up</span>
            <h3>Missed or weak criteria</h3>
            ${listMarkup(report.missedCriteria, "warning")}
          </article>
          <article class="cm-card">
            <span class="cm-eyebrow">Assumptions</span>
            <h3>Weak assumptions</h3>
            ${listMarkup(report.weakAssumptions)}
          </article>
          <article class="cm-card">
            <span class="cm-eyebrow">Evidence</span>
            <h3>Missing metrics or proof</h3>
            ${listMarkup(report.missingMetricsOrEvidence, "coral")}
          </article>
        </div>
      </section>

      <section class="cm-section">
        <div class="cm-report-detail-grid">
          <article class="cm-card">
            <span class="cm-eyebrow">Best answer</span>
            <h3>Question ${report.bestAnswer.questionNumber}</h3>
            <p>${escapeHtml(report.bestAnswer.summary)}</p>
            <strong class="cm-inline-score">${escapeHtml(report.bestAnswer.score || "n/a")}</strong>
          </article>
          <article class="cm-card">
            <span class="cm-eyebrow">Weakest answer</span>
            <h3>Question ${report.weakestAnswer.questionNumber}</h3>
            <p>${escapeHtml(report.weakestAnswer.summary)}</p>
            <strong class="cm-inline-score">${escapeHtml(report.weakestAnswer.score || "n/a")}</strong>
          </article>
        </div>
      </section>

      <section class="cm-section">
        <article class="cm-card">
          <span class="cm-eyebrow">Suggested improved answer</span>
          <div class="cm-answer-stack">
            ${report.improvedAnswers
              .map(
                (item) => `
                  <div class="cm-answer-card">
                    <h3>${escapeHtml(item.question)}</h3>
                    <p>${escapeHtml(item.suggestion)}</p>
                  </div>
                `
              )
              .join("")}
          </div>
        </article>
      </section>

      <section class="cm-section">
        <article class="cm-card">
          <span class="cm-eyebrow">Delivery feedback</span>
          <div class="cm-answer-metrics">
            <div><strong>${report.deliveryMetrics.totalFillerWords}</strong><span>total filler words</span></div>
            <div><strong>${report.deliveryMetrics.averageWordsPerMinute}</strong><span>avg typed WPM</span></div>
            <div><strong>${scores.presentationClarityScore}</strong><span>clarity score</span></div>
            <div><strong>Typed</strong><span>fallback mode</span></div>
          </div>
          <p class="cm-muted-copy">${escapeHtml(report.deliveryMetrics.note)}</p>
        </article>
      </section>
    `,
    "cm-report"
  );

  document.getElementById("copyReportBtn").addEventListener("click", copyReport);
  document.getElementById("exportReportBtn").addEventListener("click", exportReport);
  document.getElementById("restartBtn").addEventListener("click", () => {
    state.session.caseBrief = null;
    state.session.recommendationCritique = null;
    state.session.questions = [];
    state.session.answers = [];
    state.session.finalReport = null;
    state.session.timerStartedAt = null;
    saveSession();
    go("setup");
  });
}

function scoreMarkup(label, value) {
  const tone = value < 60 ? "low" : value < 76 ? "medium" : "";
  return `
    <div class="score-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}/100</strong>
      <div class="score-track ${tone}"><span style="width: ${escapeHtml(value)}%"></span></div>
    </div>
  `;
}

function reportAsText() {
  const session = state.session;
  const report = session.finalReport;
  return [
    "Case Mirror Readiness Report",
    "",
    `Case: ${session.companyName || "Untitled case"}`,
    `Overall readiness: ${report.scores.overallReadinessScore}/100`,
    `Recommendation strength: ${report.scores.recommendationStrengthScore}/100`,
    `Judge Q&A readiness: ${report.scores.qnaReadinessScore}/100`,
    `Presentation clarity: ${report.scores.presentationClarityScore}/100`,
    "",
    "Strengths:",
    ...report.strengths.map((item) => `- ${item}`),
    "",
    "Weaknesses:",
    ...report.weaknesses.map((item) => `- ${item}`),
    "",
    "Missed or weak criteria:",
    ...report.missedCriteria.map((item) => `- ${item}`),
    "",
    "Improved answer suggestion:",
    `- ${report.improvedAnswers[0]?.suggestion || "No suggestion available."}`,
    "",
    "Next practice steps:",
    ...report.nextPracticePlan.map((item) => `- ${item}`),
    "",
    "Disclaimer: This is practice feedback, not official judging or a prediction of competition results."
  ].join("\n");
}

async function copyReport() {
  try {
    await navigator.clipboard.writeText(reportAsText());
    showToast("Report copied to clipboard.");
  } catch (error) {
    showToast("Clipboard access failed. You can still export JSON.");
  }
}

function exportReport() {
  const payload = JSON.stringify(state.session.finalReport, null, 2);
  const blob = new Blob([payload], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "case-mirror-readiness-report.json";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  showToast("Report exported.");
}

function clearSession() {
  if (state.webcamStream) {
    state.webcamStream.getTracks().forEach((track) => track.stop());
    state.webcamStream = null;
  }
  state.session = createSession();
  state.setupErrors = {};
  state.error = "";
  saveSession();
  showToast("Session cleared.");
  go("home");
  render();
}

window.addEventListener("hashchange", render);
render();
