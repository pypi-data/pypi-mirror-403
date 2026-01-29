import requests
from typing import Any, Dict, Optional


class SDataClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def call_api(self, api_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/call_api"
        payload = {"api_name": api_name, "params": params or {}}
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        return resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
