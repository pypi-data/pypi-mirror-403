import json
from typing import Any, Dict
from google import genai
from google.genai import types
from .model import Model, build_content

class Gemini(Model):
    def __init__(self, api_key: str, model_name: str = "gemini-3-flash-preview"):
        super().__init__()
        self.client = None
        self.init_error = None
        self.init_error_detail = None
        if not api_key:
            self.model_name = model_name or ""
            self.init_error = "missing_api_key"
            return
        if not model_name:
            self.model_name = ""
            self.init_error = "missing_model_name"
            return
        try:
            self.client = genai.Client(api_key=api_key)
        except Exception as exc:
            self.client = None
            self.init_error = "client_init_failed"
            self.init_error_detail = repr(exc)
        self.model_name = model_name

    def evaluate(self, question: str, answer: str, prompt: str) -> Dict[str, Any]:
        if not self.client:
            return {
                "score": 0,
                "feedback": "Gemini client not initialized.",
                "issues": [
                    self.init_error_detail
                    or self.init_error
                    or "client_not_initialized"
                ],
            }

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=build_content(question, answer, prompt),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema={
                        "type": "object",
                        "properties": {
                            "score": {"type": "number"},
                            "feedback": {"type": "string"}
                        },
                        "required": ["score", "feedback"]
                    }
                )
            )
        except Exception as exc:
            return {
                "score": 0,
                "feedback": "Failed to get response from Gemini.",
                "issues": [repr(exc)],
            }

        text = (response.text or "").strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "score": 0,
                "feedback": "Model did not return valid JSON.",
                "issues": [f"invalid_json: {text}"],
            }
