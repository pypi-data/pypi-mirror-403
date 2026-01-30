import json
from typing import List
from uuid import uuid4


from accuralai_core.cli.interactive import InteractiveShell
from accuralai_core.cli.state import create_default_state
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse, Usage


def make_response(request: GenerateRequest, text: str = "ok") -> GenerateResponse:
    return GenerateResponse(
        id=request.id,
        request_id=request.id,
        output_text=text,
        finish_reason="stop",
        usage=Usage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        latency_ms=0,
    )


def build_shell(capture: List[str]):
    state = create_default_state()
    return InteractiveShell(state=state, writer=capture.append)


def test_interactive_backend_and_system_commands():
    outputs: List[str] = []
    shell = build_shell(outputs)

    shell.execute_line("/backend mock")
    shell.execute_line("/system You are helpful.")

    assert shell.state.route_hint == "mock"
    assert shell.state.system_prompt == "You are helpful."
    assert "Backend hint set" in outputs[0]
    assert "System prompt updated." in outputs[1]


def test_interactive_model_command():
    outputs: List[str] = []
    shell = build_shell(outputs)

    shell.execute_line("/model gemini-2.5-flash-lite")
    shell.execute_line("/model")
    shell.execute_line("/model reset")

    assert shell.state.parameters.get("model") is None
    assert "Model set" in outputs[0]
    assert "gemini-2.5-flash-lite" in outputs[1]
    assert "Cleared model" in outputs[3]


def test_interactive_tool_commands(tmp_path):
    outputs: List[str] = []
    shell = build_shell(outputs)

    shell.execute_line("/tool list")
    assert any("session.info" in line for line in outputs)

    outputs.clear()
    shell.execute_line("/tool run session.info")
    assert any("[tool] session.info" in line for line in outputs)

    outputs.clear()
    export_path = tmp_path / "history.jsonl"
    shell.state.history_enabled = True
    shell.state.history.append({"role": "user", "content": "hello"})
    shell.execute_line(f"/tool run history.export {export_path}")
    assert export_path.exists()
    assert any("history.export" in line for line in outputs)

    outputs.clear()
    shell.execute_line("/tool enable write.file")
    assert "write_file" in shell.state.tool_defs
    shell.execute_line("/tool disable write_file")
    assert "write_file" not in shell.state.tool_functions


def test_tool_function_call_loop(monkeypatch, tmp_path):
    outputs: List[str] = []
    shell = build_shell(outputs)

    shell.execute_line("/tool enable write.file")
    file_path = tmp_path / "note.txt"

    response_tool = GenerateResponse(
        id=uuid4(),
        request_id=uuid4(),
        output_text="[tool-call]",
        finish_reason="stop",
        usage=Usage(prompt_tokens=1, completion_tokens=0, total_tokens=1),
        latency_ms=0,
        metadata={
            "tool_calls": [
                {"name": "write_file", "arguments": {"path": str(file_path), "text": "from tool"}}
            ]
        },
        validator_events=[],
    )

    response_final = GenerateResponse(
        id=uuid4(),
        request_id=uuid4(),
        output_text="done",
        finish_reason="stop",
        usage=Usage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        latency_ms=0,
        metadata={},
        validator_events=[],
    )

    class DummyOrchestrator:
        def __init__(self, responses):
            self.responses = responses
            self.index = 0

        async def generate(self, request):
            response = self.responses[self.index]
            self.index += 1
            return response

        async def aclose(self):  # pragma: no cover - unused in tests
            return None

    dummy = DummyOrchestrator([response_tool, response_final])

    async def fake_ensure():
        return dummy

    monkeypatch.setattr(shell, "_ensure_orchestrator", fake_ensure)

    outputs.clear()
    shell.execute_line("write something")

    assert file_path.exists()
    assert file_path.read_text() == "from tool"
    assert any("done" in line for line in outputs)


def test_interactive_metadata_and_params_commands():
    outputs: List[str] = []
    shell = build_shell(outputs)

    shell.execute_line('/meta set temperature=0.5')
    shell.execute_line('/params set top_p=0.9')
    shell.execute_line('/meta list')

    assert shell.state.metadata["temperature"] == 0.5
    assert shell.state.parameters["top_p"] == 0.9
    assert 'temperature = 0.5' in outputs[-1]


def test_interactive_history_toggle_and_prompt(monkeypatch):
    outputs: List[str] = []
    shell = build_shell(outputs)
    shell.execute_line("/history on")

    class DummyOrchestrator:
        async def generate(self, request: GenerateRequest):
            return make_response(request, text=f"echo:{request.prompt}")

        async def aclose(self):
            pass

    dummy_orchestrator = DummyOrchestrator()

    async def fake_ensure_orchestrator():
        return dummy_orchestrator

    monkeypatch.setattr(shell, "_ensure_orchestrator", fake_ensure_orchestrator)

    shell.execute_line("Hello shell")

    assert any("History capture enabled." in line for line in outputs)
    assert any("echo:Hello shell" in line for line in outputs)
    assert shell.state.history_enabled is True
    assert len(shell.state.history) == 2
    assert shell.state.history[0]["role"] == "user"
    assert shell.state.history[0]["content"] == "Hello shell"
    assert shell.state.history[1]["role"] == "assistant"
    assert shell.state.history[1]["content"] == "echo:Hello shell"


def test_interactive_save(tmp_path):
    outputs: List[str] = []
    shell = build_shell(outputs)
    target = tmp_path / "session.json"

    shell.execute_line(f"/save {target}")

    data = json.loads(target.read_text())
    assert data["state"]["response_format"] == "text"
    assert any("Session saved" in line for line in outputs)


def test_interactive_multiline_prompt(monkeypatch):
    outputs: List[str] = []
    shell = build_shell(outputs)

    async def fake_loop(prompt_text: str):
        request = GenerateRequest(prompt=prompt_text)
        return make_response(request, text=prompt_text.upper())

    monkeypatch.setattr(shell, "_conversation_loop", fake_loop)
    monkeypatch.setattr(shell, "_readline", lambda primary: '"""')

    combined = shell._collect_multiline('"""')
    assert combined == ""

    # Execute multi-line prompt via direct method calls.
    shell.execute_line('"""')

    assert any("(empty prompt ignored)" in line for line in outputs)
