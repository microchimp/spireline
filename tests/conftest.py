import copy
import json
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "sts2mcp_payload_example.json"


@pytest.fixture(scope="session")
def fixture_doc() -> dict:
    return json.loads(FIXTURE.read_text())


@pytest.fixture
def combat(fixture_doc) -> dict:
    """A fresh copy of the synthetic combat payload (shaped as a ?hidden=1 read)."""
    return copy.deepcopy(fixture_doc["payloads"]["combat_hidden_read"])


@pytest.fixture
def game_over(fixture_doc) -> dict:
    return copy.deepcopy(fixture_doc["payloads"]["game_over"])
