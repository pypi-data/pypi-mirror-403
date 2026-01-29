"""AI Model Registry - Single source of truth for AI model availability."""

import requests
from typing import Optional, Dict, List, Any

__version__ = "0.1.0"

BASE_URL = "https://ai-model-registry.vercel.app"


def get_models(provider: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
    """Get all models or filter by provider/status."""
    params = {}
    if provider:
        params["provider"] = provider
    if status:
        params["status"] = status
    r = requests.get(f"{BASE_URL}/models", params=params)
    r.raise_for_status()
    return r.json()


def get_model(provider: str, model_id: str) -> Dict[str, Any]:
    """Get details for a specific model."""
    r = requests.get(f"{BASE_URL}/models/{provider}/{model_id}")
    r.raise_for_status()
    return r.json()


def get_latest(provider: str) -> str:
    """Get the recommended model ID for a provider."""
    r = requests.get(f"{BASE_URL}/latest/{provider}")
    r.raise_for_status()
    return r.json()["model_id"]


def get_providers() -> List[str]:
    """Get list of all supported providers."""
    r = requests.get(f"{BASE_URL}/providers")
    r.raise_for_status()
    return r.json()["providers"]


def is_active(provider: str, model_id: str) -> bool:
    """Check if a model is currently active."""
    try:
        model = get_model(provider, model_id)
        return model.get("status") == "active"
    except requests.HTTPError:
        return False


def get_replacement(provider: str, model_id: str) -> Optional[str]:
    """Get replacement model if current one is deprecated."""
    try:
        model = get_model(provider, model_id)
        return model.get("replacement")
    except requests.HTTPError:
        return None
