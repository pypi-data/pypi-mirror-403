from click.testing import CliRunner

from accuralai_core.cli.main import app


def test_cli_generate_uses_mock_backend():
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "generate",
            "--prompt",
            "  hello   from cli ",
            "--tag",
            "Demo",
            "--metadata",
            "topic=\"news\"",
        ],
    )

    assert result.exit_code == 0
    assert "hello from cli" in result.output
    assert "  hello   from" not in result.output
