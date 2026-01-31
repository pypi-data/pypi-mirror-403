import httpx
from typing import Any, Optional
from .config import get_config
from .utils import print_error
import sys

class APIClient:
    def __init__(self):
        self.config = get_config()
        if not self.config.api_token:
            # We allow init without token, but requests might fail if auth required
            pass

    @property
    def client(self) -> httpx.Client:
        headers = {}
        if self.config.api_token:
            headers["Authorization"] = f"Bearer {self.config.api_token}"
        
        return httpx.Client(
            base_url=self.config.api_url,
            headers=headers,
            timeout=30.0
        )

    def get(self, path: str, params: Optional[dict] = None) -> Any:
        try:
            with self.client as client:
                response = client.get(path, params=params)
                return self._handle_response(response)
        except httpx.RequestError as e:
            print_error(f"Connection error: {e}")
            sys.exit(1)

    def post(self, path: str, json: Optional[dict] = None) -> Any:
        try:
            with self.client as client:
                response = client.post(path, json=json)
                return self._handle_response(response)
        except httpx.RequestError as e:
            print_error(f"Connection error: {e}")
            sys.exit(1)
            
    def delete(self, path: str) -> Any:
        try:
            with self.client as client:
                response = client.delete(path)
                return self._handle_response(response)
        except httpx.RequestError as e:
            print_error(f"Connection error: {e}")
            sys.exit(1)

    def _handle_response(self, response: httpx.Response) -> Any:
        if response.status_code == 401:
            print_error("Authentication failed. Please run 'clusterra configure' or check your token.")
            sys.exit(1)
        
        if response.status_code == 403:
            print_error("Permission denied.")
            sys.exit(1)
            
        if response.status_code >= 400:
            try:
                error_msg = response.json().get("detail", response.text)
            except Exception:
                error_msg = response.text
            print_error(f"API Error ({response.status_code}): {error_msg}")
            sys.exit(1)

        try:
            return response.json()
        except Exception:
            return response.text
