import pytest

from accuralai_core.cli.interactive import InteractiveShell
from accuralai_core.cli.state import create_default_state
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse, Usage


def make_response(prompt: str) -> GenerateResponse:
    request = GenerateRequest(prompt=prompt)
    return GenerateResponse(
        id=request.id,
        request_id=request.id,
        output_text=f"echo:{prompt}",
        finish_reason="stop",
        usage=Usage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        latency_ms=0,
    )


@pytest.mark.parametrize("debug", [False, True])
def test_interactive_history_toggle(monkeypatch, debug):
    outputs = []
    state = create_default_state()
    shell = InteractiveShell(state=state, writer=outputs.append)
    shell.state.debug = debug

    async def fake_loop(prompt_text: str):
        return make_response(prompt_text)

    monkeypatch.setattr(shell, "_conversation_loop", fake_loop)

    shell.execute_line("/history on")
    shell.execute_line("Hello shell")

    assert any("History capture enabled." in line for line in outputs)
    assert any("echo:Hello shell" in line for line in outputs)
