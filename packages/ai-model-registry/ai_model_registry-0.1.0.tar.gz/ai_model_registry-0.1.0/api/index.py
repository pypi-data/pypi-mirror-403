from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Model Registry API",
    description="Single source of truth for AI model availability",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

MODELS = {
    "openai": {
        "gpt-4o": {
            "status": "active",
            "context": 128000,
            "updated": "2025-01-24"
        },
        "gpt-4o-mini": {
            "status": "active",
            "context": 128000,
            "updated": "2025-01-24"
        },
        "gpt-4-turbo": {
            "status": "active",
            "context": 128000,
            "updated": "2025-01-24"
        },
        "gpt-4": {
            "status": "legacy",
            "context": 8192,
            "replacement": "gpt-4o",
            "updated": "2025-01-24"
        },
        "gpt-3.5-turbo": {
            "status": "legacy",
            "context": 16385,
            "replacement": "gpt-4o-mini",
            "updated": "2025-01-24"
        },
        "o1": {
            "status": "active",
            "context": 200000,
            "updated": "2025-01-24"
        },
        "o1-mini": {
            "status": "active",
            "context": 128000,
            "updated": "2025-01-24"
        },
        "o3-mini": {
            "status": "active",
            "context": 200000,
            "updated": "2025-01-24"
        }
    },
    "anthropic": {
        "claude-sonnet-4-20250514": {
            "status": "active",
            "context": 200000,
            "updated": "2025-01-24"
        },
        "claude-haiku-4-20250514": {
            "status": "active",
            "context": 200000,
            "updated": "2025-01-24"
        },
        "claude-opus-4-20250514": {
            "status": "active",
            "context": 200000,
            "updated": "2025-01-24"
        },
        "claude-3-5-sonnet-20241022": {
            "status": "legacy",
            "context": 200000,
            "replacement": "claude-sonnet-4-20250514",
            "updated": "2025-01-24"
        },
        "claude-3-opus-20240229": {
            "status": "legacy",
            "context": 200000,
            "replacement": "claude-opus-4-20250514",
            "updated": "2025-01-24"
        },
        "claude-3-haiku-20240307": {
            "status": "legacy",
            "context": 200000,
            "replacement": "claude-haiku-4-20250514",
            "updated": "2025-01-24"
        }
    },
    "google": {
        "gemini-2.0-flash": {
            "status": "active",
            "context": 1048576,
            "updated": "2025-01-24"
        },
        "gemini-2.0-flash-lite": {
            "status": "active",
            "context": 1048576,
            "updated": "2025-01-24"
        },
        "gemini-1.5-pro": {
            "status": "active",
            "context": 2097152,
            "updated": "2025-01-24"
        },
        "gemini-1.5-flash": {
            "status": "active",
            "context": 1048576,
            "updated": "2025-01-24"
        }
    },
    "mistral": {
        "mistral-large-latest": {
            "status": "active",
            "context": 128000,
            "updated": "2025-01-24"
        },
        "mistral-small-latest": {
            "status": "active",
            "context": 32000,
            "updated": "2025-01-24"
        },
        "codestral-latest": {
            "status": "active",
            "context": 32000,
            "updated": "2025-01-24"
        }
    },
    "groq": {
        "llama-3.3-70b-versatile": {
            "status": "active",
            "context": 128000,
            "updated": "2025-01-24"
        },
        "llama-3.1-8b-instant": {
            "status": "active",
            "context": 128000,
            "updated": "2025-01-24"
        },
        "mixtral-8x7b-32768": {
            "status": "active",
            "context": 32768,
            "updated": "2025-01-24"
        }
    }
}

LATEST = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-20250514",
    "google": "gemini-2.0-flash",
    "mistral": "mistral-large-latest",
    "groq": "llama-3.3-70b-versatile"
}


@app.get("/")
def root():
    return {
        "service": "ai-model-registry",
        "version": "0.1.0",
        "endpoints": {
            "all_models": "/models",
            "by_provider": "/models?provider=openai",
            "specific_model": "/models/{provider}/{model_id}",
            "latest_model": "/latest/{provider}",
            "providers": "/providers"
        }
    }


@app.get("/providers")
def get_providers():
    return {"providers": list(MODELS.keys())}


@app.get("/models")
def get_models(provider: str = None, status: str = None):
    if provider:
        if provider not in MODELS:
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")
        models = MODELS[provider]
        if status:
            models = {k: v for k, v in models.items() if v.get("status") == status}
        return {provider: models}
    
    if status:
        filtered = {}
        for p, models in MODELS.items():
            filtered[p] = {k: v for k, v in models.items() if v.get("status") == status}
        return filtered
    
    return MODELS


@app.get("/models/{provider}/{model_id}")
def get_model(provider: str, model_id: str):
    if provider not in MODELS:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")
    if model_id not in MODELS[provider]:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    return {"provider": provider, "model_id": model_id, **MODELS[provider][model_id]}


@app.get("/latest/{provider}")
def get_latest(provider: str):
    if provider not in LATEST:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")
    model_id = LATEST[provider]
    return {
        "provider": provider,
        "model_id": model_id,
        **MODELS[provider][model_id]
    }


@app.get("/health")
def health():
    return {"status": "ok"}
