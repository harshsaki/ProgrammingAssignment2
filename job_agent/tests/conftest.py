import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest


@pytest.fixture
def profile():
    path = Path(__file__).resolve().parent.parent / "profile" / "profile.json"
    return json.loads(path.read_text())
