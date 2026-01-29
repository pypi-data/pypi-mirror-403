# AI Model Registry API

Single source of truth for AI model availability. Stop guessing which models are active or deprecated.

## Why?

AI models get updated, deprecated, or renamed constantly. This API keeps track so your agents and apps don't break.

## Quick Start

```bash
# Get all models
curl https://ai-model-registry.vercel.app/models

# Get OpenAI models only
curl https://ai-model-registry.vercel.app/models?provider=openai

# Get only active models
curl https://ai-model-registry.vercel.app/models?status=active

# Get recommended model for a provider
curl https://ai-model-registry.vercel.app/latest/anthropic
```

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | API info and available endpoints |
| `GET /providers` | List all supported providers |
| `GET /models` | Get all models (optional: `?provider=` `?status=`) |
| `GET /models/{provider}/{model_id}` | Get specific model details |
| `GET /latest/{provider}` | Get recommended model for provider |
| `GET /health` | Health check |

## Supported Providers

- OpenAI
- Anthropic
- Google
- Mistral
- Groq

## Response Example

```json
{
  "provider": "anthropic",
  "model_id": "claude-sonnet-4-20250514",
  "status": "active",
  "context": 200000,
  "updated": "2025-01-24"
}
```

## Status Values

- `active` - Current, recommended for use
- `legacy` - Still works, but newer version available
- `deprecated` - Will be removed soon

## Run Locally

```bash
pip install fastapi uvicorn
uvicorn api.index:app --reload
```

Open `http://localhost:8000/docs` for Swagger UI.

## Deploy to Vercel

```bash
npm i -g vercel
vercel
```

## For AI Agents

Add to your system prompt:
```
Before making API calls, verify model availability at https://ai-model-registry.vercel.app/latest/{provider}
```

## License

MIT
