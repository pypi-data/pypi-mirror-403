import json
from typing import Any, Dict, Optional

import requests

DEFAULT_BASE_URL = "https://api.securitytrails.com/v1"


class SecurityTrailsError(RuntimeError):
    pass


def _parse_json(value: Optional[str]) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise SecurityTrailsError(f"Invalid JSON: {exc}") from exc


def build_headers(api_key: str, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers = {
        "APIKEY": api_key,
        "Accept": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    return headers


def request(
    method: str,
    path: str,
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> requests.Response:
    if path.startswith("http://") or path.startswith("https://"):
        url = path
    else:
        if not path.startswith("/"):
            path = "/" + path
        url = base_url.rstrip("/") + path
    headers = build_headers(api_key)
    return requests.request(
        method=method.upper(),
        url=url,
        headers=headers,
        params=params,
        json=data,
        timeout=timeout,
    )
