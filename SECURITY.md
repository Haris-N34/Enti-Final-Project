# Security And Privacy

Case Mirror is a course-project MVP and should be treated as a practice tool, not a production platform.

## Secrets

Do not commit:

- `.env` files
- Qwen, Groq, Tavily, Deepgram, Hugging Face, or RunPod API keys
- private deployment credentials
- uploaded user media or generated local data

Use:

- `casecoach/backend/.env.example` for variable names
- local `.env` files for development secrets
- deployment-provider environment variables for hosted backends

## Data Handling

- The browser session is stored locally in `localStorage`.
- The local demo profile is not production authentication.
- Optional webcam and microphone features require explicit browser permission.
- Browser-side Teachable Machine outputs are summarized as coaching evidence.
- Backend upload artifacts are stored locally under the configured data directory.

## Safety Boundaries

The project must not infer or claim:

- protected traits
- emotion
- personality
- employability
- official judge scores
- competition winners

Delivery and body signals should be described only as visible, observable practice signals.

## Reporting Issues

For the course project, report security or privacy issues directly to the team before submission so the README, demo, and code can be corrected.
