import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .config import CACHE_DIR


def _cache_key(method: str, url: str, params: Optional[Dict[str, Any]], data: Optional[Dict[str, Any]]) -> str:
    payload = {
        "method": method.upper(),
        "url": url,
        "params": params or {},
        "data": data or {},
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def load_cached(method: str, url: str, params: Optional[Dict[str, Any]], data: Optional[Dict[str, Any]], ttl: int) -> Optional[Dict[str, Any]]:
    key = _cache_key(method, url, params, data)
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    ts = payload.get("ts")
    if not isinstance(ts, (int, float)):
        return None
    if ttl > 0 and (time.time() - ts) > ttl:
        return None
    return payload.get("data")


def save_cached(
    method: str,
    url: str,
    params: Optional[Dict[str, Any]],
    data: Optional[Dict[str, Any]],
    response_json: Dict[str, Any],
) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = _cache_key(method, url, params, data)
    path = _cache_path(key)
    tmp = path.with_suffix(".json.tmp")
    payload = {"ts": time.time(), "data": response_json}
    try:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(payload, f)
            f.write("\n")
        tmp.replace(path)
    except OSError:
        pass
