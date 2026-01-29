import importlib
import sys
from types import ModuleType


def _import_gemini_with_fakes(monkeypatch, response_text="{\"score\": 80, \"feedback\": \"ok\"}"):
    class FakeResponse:
        text = response_text

    class FakeModels:
        def __init__(self):
            self.calls = []

        def generate_content(self, model, contents, config):
            self.calls.append({"model": model, "contents": contents, "config": config})
            return FakeResponse()

    class FakeClient:
        def __init__(self, api_key):
            self.api_key = api_key
            self.models = FakeModels()

    fake_genai = ModuleType("google.genai")
    fake_genai.Client = FakeClient
    fake_types = ModuleType("google.genai.types")
    fake_types.GenerateContentConfig = lambda **kwargs: {"cfg": kwargs}
    google_pkg = ModuleType("google")
    google_pkg.genai = fake_genai

    monkeypatch.setitem(sys.modules, "google", google_pkg)
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setitem(sys.modules, "google.genai.types", fake_types)
    sys.modules.pop("pythonmentor.models.gemini", None)

    module = importlib.import_module("pythonmentor.models.gemini")
    module = importlib.reload(module)
    return module, FakeClient


def test_gemini_init_uses_api_key(monkeypatch):
    module, FakeClient = _import_gemini_with_fakes(monkeypatch)

    gem = module.Gemini(api_key="k-123", model_name="m-1")

    assert isinstance(gem.client, FakeClient)
    assert gem.client.api_key == "k-123"
    assert gem.model_name == "m-1"


def test_gemini_evaluate_parses_json(monkeypatch):
    module, _ = _import_gemini_with_fakes(monkeypatch)

    gem = module.Gemini(api_key="k-123", model_name="m-1")
    result = gem.evaluate("Q", "A", "P")

    assert result == {"score": 80, "feedback": "ok"}
    assert gem.client.models.calls


def test_gemini_evaluate_raises_on_invalid_json(monkeypatch):
    module, _ = _import_gemini_with_fakes(monkeypatch, response_text="not json")

    gem = module.Gemini(api_key="k-123")
    result = gem.evaluate("Q", "A", "P")

    assert result["error"] == "invalid_json"
    assert result["score"] == 0
