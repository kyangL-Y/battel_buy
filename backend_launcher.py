from __future__ import annotations

import os
import sys
from pathlib import Path


def _set_runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    else:
        base_dir = Path(__file__).resolve().parent
    os.environ.setdefault("BATTEL_APP_BASE_DIR", str(base_dir))
    return base_dir


def main() -> None:
    _set_runtime_base_dir()

    import uvicorn

    from api.app import app

    host = os.environ.get("BATTEL_HOST", "127.0.0.1")
    port = int(os.environ.get("BATTEL_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
