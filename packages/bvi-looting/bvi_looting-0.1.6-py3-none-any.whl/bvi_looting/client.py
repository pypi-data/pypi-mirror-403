import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

import requests


def _prompt_password() -> str:
    """Запросить пароль в терминале (без отображения)."""
    if sys.stdin.isatty():
        try:
            import getpass
            return (getpass.getpass("BVI password: ") or "").strip()
        except Exception:
            pass
    return input("BVI password: ").strip()


class BviLootingClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        session_id: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 300,
        solutions_dir: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.session_id = session_id or str(uuid4())
        self.password = password
        self.timeout = timeout
        self.solutions_dir = solutions_dir or os.environ.get("BVI_SOLUTIONS_DIR", "solutions").strip() or "solutions"

    def _ensure_password(self) -> None:
        """Если пароль не задан — запросить один раз в терминале."""
        if not self.password:
            self.password = _prompt_password()

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
        self._ensure_password()
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
        code = data.get("code", "")
        explanation = data.get("explanation", "")
        solution_content = data.get("solution_content") or f"{code}\n\n---\n\n{explanation}"
        local_solution_file = ""
        dir_path = Path(self.solutions_dir)
        if solution_content.strip():
            dir_path.mkdir(parents=True, exist_ok=True)
            stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_sid = "".join(c if c.isalnum() or c in "-_" else "_" for c in self.session_id)[:32]
            filename = f"{safe_sid}_{stamp}.txt"
            file_path = dir_path / filename
            file_path.write_text(solution_content, encoding="utf-8")
            local_solution_file = str(file_path)
        return {
            "session_id": self.session_id,
            "code": code,
            "explanation": explanation,
            "solution_file": data.get("solution_file", ""),
            "local_solution_file": local_solution_file,
        }

    def get_history(self, session_id: Optional[str] = None) -> dict:
        self._ensure_password()
        url = f"{self.base_url}/history"
        params = {"session_id": session_id if session_id is not None else self.session_id}
        r = requests.get(url, params=params, headers=self._headers(), timeout=self.timeout, proxies=self._proxies())
        r.raise_for_status()
        return r.json()

    def health(self) -> bool:
        self._ensure_password()
        try:
            r = requests.get(f"{self.base_url}/health", headers=self._headers(), timeout=5, proxies=self._proxies())
            return r.status_code == 200
        except Exception:
            return False
