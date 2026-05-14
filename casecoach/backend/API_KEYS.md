# API Keys And Model Access

The backend can run without remote model keys, but Qwen live preparation, answer grading, and final report synthesis will be skipped until these values are configured.

Important: the project's Teachable Machine model does not use an API key. It is a browser-loaded image model stored directly in the frontend at `case-mirror/assets/teachable-image/`. The backend only receives the summarized `teachable_*` outputs from the browser.

## Qwen3-VL / Qwen3-Omni through Alibaba Cloud Model Studio

Use this when you want Alibaba-hosted Qwen models through an OpenAI-compatible endpoint.

- API key docs: https://www.alibabacloud.com/help/en/model-studio/get-api-key
- Model Studio console: https://bailian.console.alibabacloud.com/
- Visual reasoning docs: https://www.alibabacloud.com/help/en/model-studio/usage-of-visual-reasoning-models

Set:

```bash
QWEN_VL_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_VL_API_KEY=your_key_here
QWEN_VL_MODEL=qwen3.6-plus
```

If `QWEN_VL_MODEL` is a numeric Alibaba Model Studio application ID, such as `210965`, the backend automatically calls the DashScope application endpoint instead:

```text
https://dashscope-intl.aliyuncs.com/api/v1/apps/{APP_ID}/completion
```

Use numeric IDs for Model Studio Applications. Use model names such as `qwen-plus` or a Qwen model ID for OpenAI-compatible `/chat/completions`.

For the current live rehearsal setup, use:

```bash
QWEN_VL_MODEL=qwen3.6-plus
```

## Optional Groq Secondary Report Fallback

Qwen is the primary live report model. Use Groq only when you want a secondary OpenAI-compatible provider if Qwen report synthesis fails.

- API docs: https://console.groq.com/docs/overview

Set:

```bash
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=gpt-oss-120b
```

Optional market research uses Tavily:

- API docs: https://docs.tavily.com/documentation/api-reference/endpoint/search

```bash
TAVILY_API_KEY=your_tavily_key_here
```

Live speech transcription uses Deepgram temporary tokens:

- Token auth docs: https://developers.deepgram.com/guides/fundamentals/token-based-authentication
- Live audio WebSocket docs: https://developers.deepgram.com/reference/speech-to-text/listen-streaming

```bash
DEEPGRAM_API_KEY=your_deepgram_key_here
```

Alibaba documents these OpenAI-compatible base URLs by region:

- Singapore: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- US Virginia: `https://dashscope-us.aliyuncs.com/compatible-mode/v1`
- China Beijing: `https://dashscope.aliyuncs.com/compatible-mode/v1`

## Hugging Face Tokens

Use this when downloading gated/private model weights, using Hugging Face inference, or adding pyannote diarization.

- Access tokens: https://huggingface.co/settings/tokens
- Token docs: https://huggingface.co/docs/hub/security-tokens
- pyannote Community-1 model terms: https://huggingface.co/pyannote/speaker-diarization-community-1

For pyannote Community-1, accept the model terms on Hugging Face and create a token with read access.

## RunPod GPU Infrastructure

Use this if you self-host Qwen3-VL/Qwen3-Omni on a remote GPU and expose an OpenAI-compatible endpoint.

- API docs: https://docs.runpod.io/api-reference/
- API keys are in the RunPod console under Settings > API Keys.

The CaseCoach backend does not call RunPod directly yet. If you deploy a vLLM/SGLang server on RunPod, put that server's endpoint and bearer token into `QWEN_VL_BASE_URL` and `QWEN_VL_API_KEY`.
