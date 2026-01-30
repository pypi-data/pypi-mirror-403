import json
import os
import subprocess
from typing import Any, Dict, Optional

import requests

from .errors import ApiError, ConfigError


class GitHubClient:
    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com") -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token or _get_token()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "User-Agent": "gh-task",
            }
        )

    def rest(self, method: str, path: str, *, params: Optional[Dict[str, Any]] = None, json_body: Any = None) -> Any:
        url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"
        resp = self.session.request(method, url, params=params, json=json_body)
        if resp.status_code >= 400:
            raise ApiError(resp.status_code, _safe_payload(resp))
        if resp.text:
            return resp.json()
        return None

    def graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {"query": query, "variables": variables or {}}
        resp = self.session.post(f"{self.base_url}/graphql", data=json.dumps(payload))
        if resp.status_code >= 400:
            raise ApiError(resp.status_code, _safe_payload(resp))
        data = resp.json()
        if data.get("errors"):
            raise ApiError(resp.status_code, data["errors"])
        return data["data"]


def _get_token() -> str:
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if token:
        return token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as exc:
        raise ConfigError("GitHub token not set and gh not found in PATH") from exc
    except subprocess.CalledProcessError as exc:
        raise ConfigError("GitHub token not set and gh auth token failed") from exc
    token = result.stdout.strip()
    if not token:
        raise ConfigError("GitHub token is empty")
    return token


def _safe_payload(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except ValueError:
        return resp.text
