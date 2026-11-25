"""Storage for collections, history, and environment variables."""
import json
import os
from pathlib import Path
from typing import Any
from .models import Request, Collection


CONFIG_DIR = Path.home() / ".config" / "api-tester-tui"
COLLECTIONS_FILE = CONFIG_DIR / "collections.json"
HISTORY_FILE = CONFIG_DIR / "history.json"
ENV_FILE = CONFIG_DIR / "env.json"


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_collections() -> dict[str, Collection]:
    ensure_config_dir()
    if not COLLECTIONS_FILE.exists():
        return {}
    try:
        data = json.loads(COLLECTIONS_FILE.read_text())
        collections = {}
        for name, coll_data in data.items():
            requests = [Request(**r) for r in coll_data.get("requests", [])]
            collections[name] = Collection(
                name=name,
                requests=requests,
                base_url=coll_data.get("base_url", ""),
                headers=coll_data.get("headers", {}),
            )
        return collections
    except Exception:
        return {}


def save_collections(collections: dict[str, Collection]):
    ensure_config_dir()
    data = {}
    for name, coll in collections.items():
        data[name] = {
            "base_url": coll.base_url,
            "headers": coll.headers,
            "requests": [
                {
                    "method": r.method,
                    "url": r.url,
                    "headers": r.headers,
                    "params": r.params,
                    "body": r.body,
                    "body_type": r.body_type,
                }
                for r in coll.requests
            ],
        }
    COLLECTIONS_FILE.write_text(json.dumps(data, indent=2))


def load_history(limit: int = 100) -> list[dict[str, Any]]:
    ensure_config_dir()
    if not HISTORY_FILE.exists():
        return []
    try:
        history = json.loads(HISTORY_FILE.read_text())
        return history[-limit:]
    except Exception:
        return []


def save_history(entry: dict[str, Any]):
    ensure_config_dir()
    history = load_history(limit=500)
    history.append(entry)
    HISTORY_FILE.write_text(json.dumps(history[-500:], indent=2))


def load_env() -> dict[str, str]:
    ensure_config_dir()
    if not ENV_FILE.exists():
        return {}
    try:
        return json.loads(ENV_FILE.read_text())
    except Exception:
        return {}


def save_env(env: dict[str, str]):
    ensure_config_dir()
    ENV_FILE.write_text(json.dumps(env, indent=2))


def interpolate(text: str, env: dict[str, str]) -> str:
    """Replace ${VAR} with environment values."""
    import re
    def repl(match):
        var = match.group(1)
        return env.get(var, match.group(0))
    return re.sub(r"\$\{(\w+)\}", repl, text)