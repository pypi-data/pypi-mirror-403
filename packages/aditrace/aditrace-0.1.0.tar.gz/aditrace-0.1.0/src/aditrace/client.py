import traceback
import uuid
from datetime import datetime
from typing import Dict, Any

import requests


class AdiTraceClient:

    def __init__(self, app_key: str, env: str) -> None:
        self.app_key = app_key
        self.env = env

    def _build_payload(self, error: Exception) -> Dict[str, Any]:
        try:
            payload = {
                "meta": {
                    "event_id": str(uuid.uuid4()),
                    "timestamp": datetime.now(),
                    "environment": self.env,
                },
                "error": {
                    "type": type(error).__name__,
                    "message": str(error),
                    "stacktrace": traceback.format_exc(),
                    "handled": False,
                },
            }

            return payload
        except Exception as e:
            raise e

    def __call__(self, error: Exception):
        try:
            payload: Dict[str, any] = self._build_payload(error)

            headers: Dict[str, any] = {
                "Content-Type": "application/json",
                "App-Key": self.app_key,
            }
            url: str = "https://api.aditrace.com/v1/events/"
            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                pass
        except Exception as e:
            raise e