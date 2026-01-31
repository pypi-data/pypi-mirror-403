import os
from pathlib import Path
from typing import Optional

from bvi_looting.client import BviLootingClient

__all__ = ["BviLootingClient", "solve"]
__version__ = "0.1.6"

_default_client = None  # type: Optional[BviLootingClient]


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


def solve(task: str, lang: str = "python", base_url: str = 'http://192.168.1.125:8000') -> dict:
    """Решить задачу. base_url — адрес сервера (например http://192.168.1.5:8000); если не задан — из BVI_BASE_URL или localhost."""
    if base_url and base_url.strip():
        c = BviLootingClient(base_url=base_url.strip())
        return c.solve(task=task, lang=lang)
    return _get_client().solve(task=task, lang=lang)
