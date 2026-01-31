import requests
from typing import Any, Dict
from .exceptions import APIError

DEFAULT_BASE_URL = "https://www.waterworks.ai/api"


class WaterworksClient:
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL, timeout: int = 60):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def post(self, endpoint: str, payload: Dict[str, Any]) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        payload = dict(payload)
        payload["api_key"] = self.api_key

        resp = requests.post(url, json=payload, timeout=self.timeout)

        if resp.status_code != 200:
            raise APIError(f"{resp.status_code}: {resp.text}")

        return resp.json()
