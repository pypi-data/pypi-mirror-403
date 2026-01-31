import requests
from typing import Optional
from uuid import uuid4


class BviLootingClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        session_id: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 300,
    ):
        self.base_url = base_url.rstrip("/")
        self.session_id = session_id or str(uuid4())
        self.password = password
        self.timeout = timeout

    def _headers(self) -> dict:
        h = {}
        if self.password:
            h["Authorization"] = f"Bearer {self.password}"
        return h

    def _proxies(self) -> dict:
        if "127.0.0.1" in self.base_url or "localhost" in self.base_url.lower():
            return {"http": None, "https": None}
        return {}

    def solve(self, task: str, lang: str = 'python') -> dict:
        url = f"{self.base_url}/solve"
        payload = {"task": task, "session_id": self.session_id, "lang": lang}
        try:
            r = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout, proxies=self._proxies())
        except requests.exceptions.ReadTimeout:
            raise TimeoutError(
                f"Сервер не ответил за {self.timeout} с. Ответ Gemini может занимать много времени — попробуйте ещё раз или увеличьте timeout в BviLootingClient(timeout=...)."
            ) from None
        r.raise_for_status()
        data = r.json()
        self.session_id = data.get("session_id", self.session_id)
        return {
            "session_id": self.session_id,
            "code": data.get("code", ""),
            "explanation": data.get("explanation", ""),
            "solution_file": data.get("solution_file", ""),
        }

    def get_history(self, session_id: Optional[str] = None) -> dict:
        url = f"{self.base_url}/history"
        params = {"session_id": session_id if session_id is not None else self.session_id}
        r = requests.get(url, params=params, headers=self._headers(), timeout=self.timeout, proxies=self._proxies())
        r.raise_for_status()
        return r.json()

    def health(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/health", headers=self._headers(), timeout=5, proxies=self._proxies())
            return r.status_code == 200
        except Exception:
            return False
