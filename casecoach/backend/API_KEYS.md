# API Keys And Model Access

The backend can run without remote model keys, but Qwen reasoning will be skipped until these values are configured.

## Qwen3-VL / Qwen3-Omni through Alibaba Cloud Model Studio

Use this when you want Alibaba-hosted Qwen models through an OpenAI-compatible endpoint.

- API key docs: https://www.alibabacloud.com/help/en/model-studio/get-api-key
- Model Studio console: https://bailian.console.alibabacloud.com/
- Visual reasoning docs: https://www.alibabacloud.com/help/en/model-studio/usage-of-visual-reasoning-models

Set:

```bash
QWEN_VL_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_VL_API_KEY=your_key_here
QWEN_VL_MODEL=Qwen/Qwen3-VL-8B-Instruct
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

