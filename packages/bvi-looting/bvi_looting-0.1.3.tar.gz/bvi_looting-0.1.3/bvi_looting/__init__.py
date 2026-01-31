import os
from pathlib import Path

from bvi_looting.client import BviLootingClient

__all__ = ["BviLootingClient", "solve"]
__version__ = "0.1.3"

_default_client: BviLootingClient | None = None


def _get_client() -> BviLootingClient:
    global _default_client
    if _default_client is not None:
        return _default_client
    try:
        from dotenv import load_dotenv
        for p in (Path.cwd(), Path(__file__).resolve().parent.parent):
            env = p / ".env"
            if env.exists():
                load_dotenv(env)
                break
        else:
            load_dotenv()
    except Exception:
        pass
    base = os.environ.get("BVI_BASE_URL", "http://127.0.0.1:8000").strip()
    password = os.environ.get("BVI_PASSWORD", "").strip()
    timeout = int(os.environ.get("BVI_TIMEOUT", "300"))
    solutions_dir = os.environ.get("BVI_SOLUTIONS_DIR", "").strip() or None
    _default_client = BviLootingClient(base_url=base, password=password or None, timeout=timeout, solutions_dir=solutions_dir)
    return _default_client


def solve(task: str, lang: str = "python") -> dict:
    return _get_client().solve(task=task, lang=lang)
