"""Authentication storage for wafer CLI.

Stores API keys for various providers (RunPod, DigitalOcean, Modal) in
~/.wafer/auth.json. Environment variables take precedence over stored
credentials.

Usage:
    from wafer_core.auth import get_api_key, save_api_key, remove_api_key

    # Get API key (checks env var first, then auth.json)
    key = get_api_key("runpod")

    # Save API key to auth.json
    save_api_key("runpod", "rp_xxx...")

    # Remove API key from auth.json
    remove_api_key("runpod")
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

# Provider configurations
PROVIDERS = {
    "runpod": {
        "env_var": "WAFER_RUNPOD_API_KEY",
        "display_name": "RunPod",
        "key_url": "https://runpod.io/console/user/settings",
    },
    "digitalocean": {
        "env_var": "WAFER_AMD_DIGITALOCEAN_API_KEY",
        "display_name": "DigitalOcean AMD",
        "key_url": "https://cloud.digitalocean.com/account/api/tokens",
    },
    "modal": {
        "env_var": "MODAL_TOKEN_ID",  # Modal uses token ID + secret
        "display_name": "Modal",
        "key_url": "https://modal.com/settings",
    },
    "anthropic": {
        "env_var": "ANTHROPIC_API_KEY",
        "alt_env_var": "WAFER_ANTHROPIC_API_KEY",  # Check this first
        "display_name": "Anthropic",
        "key_url": "https://console.anthropic.com/settings/keys",
    },
    "openai": {
        "env_var": "OPENAI_API_KEY",
        "alt_env_var": "WAFER_OPENAI_KEY",  # Check this first
        "display_name": "OpenAI",
        "key_url": "https://platform.openai.com/api-keys",
    },
}


def get_wafer_home() -> Path:
    """Get the wafer home directory (~/.wafer)."""
    return Path.home() / ".wafer"


def get_auth_file() -> Path:
    """Get the path to the auth.json file."""
    return get_wafer_home() / "auth.json"


def _load_auth_json() -> dict:
    """Load auth.json, returning empty dict if not found."""
    auth_file = get_auth_file()
    if not auth_file.exists():
        return {}
    try:
        return json.loads(auth_file.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_auth_json(data: dict) -> None:
    """Save auth.json, creating directory if needed."""
    auth_file = get_auth_file()
    auth_file.parent.mkdir(parents=True, exist_ok=True)
    # Set restrictive permissions (owner read/write only)
    auth_file.write_text(json.dumps(data, indent=2))
    auth_file.chmod(0o600)


def get_api_key(provider: str) -> str | None:
    """Get API key for a provider.

    Checks in order:
    1. Alt environment variable if defined (e.g., WAFER_ANTHROPIC_API_KEY)
    2. Primary environment variable (e.g., ANTHROPIC_API_KEY)
    3. ~/.wafer/auth.json

    Args:
        provider: Provider name (runpod, digitalocean, modal, anthropic, openai)

    Returns:
        API key string or None if not found
    """
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}. Valid: {list(PROVIDERS.keys())}")

    config = PROVIDERS[provider]

    # Check alt environment variable first (e.g., WAFER_ANTHROPIC_API_KEY)
    if "alt_env_var" in config:
        alt_key = os.environ.get(config["alt_env_var"], "").strip()
        if alt_key:
            return alt_key

    # Check primary environment variable
    env_key = os.environ.get(config["env_var"], "").strip()
    if env_key:
        return env_key

    # Check auth.json
    auth_data = _load_auth_json()
    provider_data = auth_data.get(provider, {})
    return provider_data.get("api_key")


def save_api_key(provider: str, api_key: str) -> None:
    """Save API key for a provider to ~/.wafer/auth.json.

    Args:
        provider: Provider name (runpod, digitalocean, modal)
        api_key: The API key to save
    """
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}. Valid: {list(PROVIDERS.keys())}")

    auth_data = _load_auth_json()
    auth_data[provider] = {"api_key": api_key}
    _save_auth_json(auth_data)


def remove_api_key(provider: str) -> bool:
    """Remove API key for a provider from ~/.wafer/auth.json.

    Args:
        provider: Provider name (runpod, digitalocean, modal)

    Returns:
        True if key was removed, False if it didn't exist
    """
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}. Valid: {list(PROVIDERS.keys())}")

    auth_data = _load_auth_json()
    if provider in auth_data:
        del auth_data[provider]
        _save_auth_json(auth_data)
        return True
    return False


@dataclass
class AuthStatus:
    """Status of authentication for a provider."""

    provider: str
    display_name: str
    is_authenticated: bool
    source: str | None  # "env" or "file" or None
    key_preview: str | None  # e.g., "rp_xxx...abc"
    key_url: str


def get_auth_status(provider: str) -> AuthStatus:
    """Get authentication status for a provider.

    Args:
        provider: Provider name (runpod, digitalocean, modal, anthropic, openai)

    Returns:
        AuthStatus with details about the auth state
    """
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}. Valid: {list(PROVIDERS.keys())}")

    config = PROVIDERS[provider]

    # Check alt environment variable first (e.g., WAFER_ANTHROPIC_API_KEY)
    if "alt_env_var" in config:
        alt_key = os.environ.get(config["alt_env_var"], "").strip()
        if alt_key:
            return AuthStatus(
                provider=provider,
                display_name=config["display_name"],
                is_authenticated=True,
                source="env",
                key_preview=_format_key_preview(alt_key),
                key_url=config["key_url"],
            )

    # Check primary environment variable
    env_key = os.environ.get(config["env_var"], "").strip()
    if env_key:
        return AuthStatus(
            provider=provider,
            display_name=config["display_name"],
            is_authenticated=True,
            source="env",
            key_preview=_format_key_preview(env_key),
            key_url=config["key_url"],
        )

    # Check auth.json
    auth_data = _load_auth_json()
    provider_data = auth_data.get(provider, {})
    file_key = provider_data.get("api_key")

    if file_key:
        return AuthStatus(
            provider=provider,
            display_name=config["display_name"],
            is_authenticated=True,
            source="file",
            key_preview=_format_key_preview(file_key),
            key_url=config["key_url"],
        )

    return AuthStatus(
        provider=provider,
        display_name=config["display_name"],
        is_authenticated=False,
        source=None,
        key_preview=None,
        key_url=config["key_url"],
    )


def get_all_auth_status() -> list[AuthStatus]:
    """Get authentication status for all providers."""
    return [get_auth_status(provider) for provider in PROVIDERS]


def _format_key_preview(key: str) -> str:
    """Format API key for safe display (e.g., 'rp_xxx...abc')."""
    if len(key) <= 12:
        return "***"
    return f"{key[:6]}...{key[-4:]}"
