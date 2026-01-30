import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
CORE_PATH = ROOT / "packages" / "accuralai-core"
GOOGLE_PATH = ROOT / "packages" / "accuralai-google"

for path in (CORE_PATH, GOOGLE_PATH):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


@pytest.fixture(autouse=True)
def ensure_api_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_GENAI_API_KEY", "test-key")
    yield
    os.environ.pop("GOOGLE_GENAI_API_KEY", None)


@pytest.fixture
def anyio_backend():
    return "asyncio"
