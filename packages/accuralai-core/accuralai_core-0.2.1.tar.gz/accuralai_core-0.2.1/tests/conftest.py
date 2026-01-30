import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = ROOT
CANONICALIZE_PATH = Path(__file__).resolve().parents[3] / "accuralai-canonicalize"

for path in {CORE_PATH, CANONICALIZE_PATH}:
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))


@pytest.fixture
def anyio_backend():
    return "asyncio"
