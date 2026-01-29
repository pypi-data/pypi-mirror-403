import ast
from pathlib import Path


def _load_run_one(fake_globals):
    source = Path("src/models/vertex.py").read_text(encoding="utf-8")
    module_ast = ast.parse(source)
    func_node = next(
        node for node in module_ast.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_one"
    )
    code = ast.Module(body=[func_node], type_ignores=[])
    compiled = compile(code, "src/models/vertex.py", "exec")
    namespace = dict(fake_globals)
    exec(compiled, namespace)
    return namespace["run_one"]


class FakeTime:
    def __init__(self):
        self.now = 100.0
        self.sleeps = []

    def time(self):
        return self.now

    def sleep(self, secs):
        self.sleeps.append(secs)
        self.now += secs


class FakeRandom:
    @staticmethod
    def random():
        return 0.5


def test_run_one_success():
    class FakeResponse:
        text = "hello world"

    class FakeModel:
        def generate_content(self, prompt, generation_config):
            return FakeResponse()

    fake_time = FakeTime()
    run_one = _load_run_one({
        "PROMPT": "prompt",
        "MAX_RETRIES": 3,
        "model": FakeModel(),
        "INIT_ERROR": None,
        "time": fake_time,
        "random": FakeRandom(),
    })

    result = run_one(1)

    assert result["ok"] is True
    assert result["words"] == 2
    assert result["attempt"] == 1
    assert result["id"] == 1


def test_run_one_retries_and_fails():
    class FakeModel:
        def generate_content(self, prompt, generation_config):
            raise RuntimeError("boom")

    fake_time = FakeTime()
    run_one = _load_run_one({
        "PROMPT": "prompt",
        "MAX_RETRIES": 2,
        "model": FakeModel(),
        "INIT_ERROR": None,
        "time": fake_time,
        "random": FakeRandom(),
    })

    result = run_one(9)

    assert result["ok"] is False
    assert result["id"] == 9
    assert "RuntimeError" in result["error"]
    assert len(fake_time.sleeps) == 2
