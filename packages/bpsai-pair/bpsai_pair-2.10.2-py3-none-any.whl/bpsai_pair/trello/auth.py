"""
Trello authentication - compatible with CodexAgent-Trello token storage.
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any

TOKENS_FOLDER = Path.home() / ".trello_codex_tokens"
TOKEN_FILE = TOKENS_FOLDER / "trello_token.json"
TOKEN_STORE_VERSION = 2


def ensure_token_dir() -> None:
    """Ensure the token directory exists."""
    TOKENS_FOLDER.mkdir(exist_ok=True)


def store_token(token: str, api_key: str) -> None:
    """Store Trello credentials.

    Args:
        token: Trello API token
        api_key: Trello API key
    """
    ensure_token_dir()
    payload = {
        "token": token,
        "api_key": api_key,
        "version": TOKEN_STORE_VERSION,
    }
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)


def load_token() -> Optional[Dict[str, Any]]:
    """Load stored Trello credentials.

    Returns:
        Dict with token, api_key, version if found, None otherwise
    """
    try:
        with open(TOKEN_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("token") and data.get("api_key"):
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return None


def clear_token() -> None:
    """Remove stored Trello credentials."""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


def is_connected() -> bool:
    """Check if Trello credentials are stored.

    Returns:
        True if credentials exist, False otherwise
    """
    return load_token() is not None
