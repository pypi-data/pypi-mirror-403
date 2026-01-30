from __future__ import annotations

from dataclasses import dataclass
import shutil

from pathlib import Path

from .extractor.unzipper import resolve_input_path, get_last_error
from .models.gemini import Gemini
from .dir.checker import get_file_by_type
from .processors.processor import combine


@dataclass
class PythonMentor:
    api_key: str
    model_name: str = "gemini-3-flash-preview"

    def __post_init__(self) -> None:
        self.tutor = None
        self.init_error = None
        if not self.api_key:
            self.init_error = "missing_api_key"
            return
        if not self.model_name:
            self.init_error = "missing_model_name"
            return
        try:
            self.tutor = Gemini(api_key=self.api_key, model_name=self.model_name)
        except Exception:
            self.init_error = "gemini_init_failed"

    def mark_submission(self, answer_path: str, question: str, prompt: str = "") -> dict:

        if not answer_path:
            return {"score": 0, "feedback": "answer_path is required.", "error": "missing_answer_path"}
        if question is None:
            return {"score": 0, "feedback": "question is required.", "error": "missing_question"}
        if self.init_error:
            feedback = {
                "missing_api_key": "api key not provided.",
                "missing_model_name": "model name not provided.",
                "gemini_init_failed": "failed to initialize Gemini client.",
            }.get(self.init_error, "Gemini is not initialized.")
            return {"score": 0, "feedback": feedback, "error": self.init_error}
        if not self.tutor:
            return {"score": 0, "feedback": "Gemini is not initialized.", "error": "gemini_not_initialized"}

        input_path, is_temp = resolve_input_path(answer_path)

        try:
            if not input_path:
                unzip_error = get_last_error() or "invalid_input_path"
                return {
                    "score": 0,
                    "feedback": f"Input path error: {unzip_error}.",
                    "error": unzip_error,
                }
            if not Path(input_path).exists():
                return {
                    "score": 0,
                    "feedback": "Input path does not exist.",
                    "error": "input_path_not_found",
                }

            answer = combine(input_path)

            python_file = get_file_by_type(input_path, ".py")
            notebook_file = get_file_by_type(input_path, ".ipynb")

            if not (python_file or notebook_file):
                return {
                    "score": 0,
                    "feedback": "No .py or .ipynb files found in the input.",
                    "error": "no_supported_files",
                }

            feedback = self.tutor.evaluate(question=question, answer=answer, prompt=prompt)
            if not answer.strip():
                feedback = {**feedback, "warning": "no_readable_content"}
            return feedback
        finally:
            if is_temp:
                shutil.rmtree(input_path, ignore_errors=True)
