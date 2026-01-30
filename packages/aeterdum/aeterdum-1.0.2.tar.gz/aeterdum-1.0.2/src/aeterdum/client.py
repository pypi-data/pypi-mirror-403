import httpx
import os
from typing import Any, Dict, Optional, Union
from .resources.logs import Logs

class Aeterdum:
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 base_url: Optional[str] = None, 
                 timeout: float = 10.0,
                 server_public_key: Optional[str] = None):
        
        self.api_key = api_key or os.environ.get("AETERDUM_API_KEY")
        if not self.api_key:
            raise ValueError("Aeterdum API Key is required")
            
        self.base_url = (base_url or "https://us.aeterdum.com").rstrip("/")
        self.timeout = timeout
        self.server_public_key = server_public_key
        
        # Resources
        self.logs = Logs(self)
        
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "aeterdum-python/1.0.0"
            },
            timeout=timeout
        )

    def request(self, method: str, path: str, **kwargs) -> Any:
        response = self._client.request(method, path, **kwargs)
        
        if not response.is_success:
            try:
                error_body = response.json()
                msg = error_body.get("message") or error_body.get("msg") or str(error_body)
            except Exception:
                msg = response.text
            
            raise Exception(f"Aeterdum API Error: {response.status_code} {msg}")
            
        return response.json()

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
