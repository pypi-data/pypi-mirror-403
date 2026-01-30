from typing import List


from accuralai_core.cli.interactive import InteractiveShell
from accuralai_core.cli.state import create_default_state


def test_tool_reload_and_info(monkeypatch):
    outputs: List[str] = []
    shell = InteractiveShell(state=create_default_state(), writer=outputs.append)

    shell.execute_line("/tool reload")
    assert any("Reloaded tool registry" in line for line in outputs)

    outputs.clear()
    shell.execute_line("/tool info session.info")
    assert any("Name: session.info" in line for line in outputs)


def test_tool_run_unknown():
    outputs: List[str] = []
    shell = InteractiveShell(state=create_default_state(), writer=outputs.append)

    shell.execute_line("/tool run missing")
    assert any("not found" in line for line in outputs)
