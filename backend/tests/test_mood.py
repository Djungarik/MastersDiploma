"""Tests for /api/analyze-mood: validation of the model answer and error handling."""

import json
from types import SimpleNamespace

import pytest

from app.config import Settings
from app.routers import mood

TEXT = "We enter the dark ancient dungeon, torchlight flickering on the damp walls"


class FakeClient:
    """Stands in for AsyncOpenAI: returns a prepared answer or raises."""

    def __init__(self, content=None, error=None):
        self._content = content
        self._error = error
        self.calls = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    async def _create(self, **kwargs):
        self.calls += 1
        if self._error:
            raise self._error
        message = SimpleNamespace(content=self._content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


@pytest.fixture()
def configure(monkeypatch):
    """Use fixed settings and a fake provider client."""

    def _configure(content=None, error=None, groq_api_key="test-key"):
        settings = Settings(ai_provider="groq", groq_api_key=groq_api_key, openai_api_key="")
        fake = FakeClient(content=content, error=error)
        monkeypatch.setattr(mood, "get_settings", lambda: settings)
        monkeypatch.setattr(mood, "create_client", lambda api_key, base_url: fake)
        return fake

    return _configure


def answer(**overrides):
    data = {"mood": "mystery", "intensity": 5, "environment": "dungeon", "reasoning": "Dark dungeon"}
    data.update(overrides)
    return json.dumps(data)


def test_valid_answer_is_returned(client, configure):
    configure(content=answer())
    response = client.post("/api/analyze-mood", json={"text": TEXT})
    assert response.status_code == 200
    assert response.json() == {
        "mood": "mystery", "intensity": 5, "environment": "dungeon", "reasoning": "Dark dungeon",
    }


def test_answer_in_markdown_block_is_parsed(client, configure):
    configure(content="```json\n" + answer(mood="epic", intensity=8) + "\n```")
    response = client.post("/api/analyze-mood", json={"text": TEXT})
    assert response.status_code == 200
    assert response.json()["mood"] == "epic"


def test_category_case_is_normalised(client, configure):
    configure(content=answer(mood=" Spooky ", environment="DUNGEON"))
    response = client.post("/api/analyze-mood", json={"text": TEXT})
    assert response.status_code == 200
    assert response.json()["mood"] == "spooky"
    assert response.json()["environment"] == "dungeon"


@pytest.mark.parametrize("overrides", [
    {"mood": "battle"},
    {"mood": None},
    {"environment": "spaceship"},
    {"intensity": 0},
    {"intensity": 11},
    {"intensity": "high"},
])
def test_values_outside_allowed_sets_are_rejected(client, configure, overrides):
    configure(content=answer(**overrides))
    response = client.post("/api/analyze-mood", json={"text": TEXT})
    assert response.status_code == 502
    assert response.json()["detail"] == "Invalid model response"


@pytest.mark.parametrize("content", ["not a json at all", "", "[1, 2, 3]"])
def test_unparseable_answer_is_rejected(client, configure, content):
    configure(content=content)
    response = client.post("/api/analyze-mood", json={"text": TEXT})
    assert response.status_code == 502


def test_provider_failure_returns_502(client, configure):
    configure(error=TimeoutError("provider timeout"))
    response = client.post("/api/analyze-mood", json={"text": TEXT})
    assert response.status_code == 502
    assert "unavailable" in response.json()["detail"]


def test_short_text_returns_400_without_calling_provider(client, configure):
    fake = configure(content=answer())
    response = client.post("/api/analyze-mood", json={"text": "too short"})
    assert response.status_code == 400
    assert fake.calls == 0


def test_empty_text_returns_422(client, configure):
    configure(content=answer())
    assert client.post("/api/analyze-mood", json={"text": ""}).status_code == 422


def test_missing_api_key_returns_503(client, configure):
    configure(content=answer(), groq_api_key="")
    assert client.post("/api/analyze-mood", json={"text": TEXT}).status_code == 503


def test_mock_endpoint_classifies_by_keywords(client):
    response = client.post("/api/analyze-mood/mock", json={"text": "The dragon attacks, draw your sword!"})
    assert response.status_code == 200
    assert response.json()["mood"] == "epic"
