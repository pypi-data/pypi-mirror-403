import os
from click.testing import CliRunner
from ai_context_core.cli import cli


def test_init_command_with_qgis_profile():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["init", "--profile", "qgis"])
        assert result.exit_code == 0
        assert os.path.exists(".ai-context/config.yaml")


def test_init_command_with_generic_profile():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert not os.path.exists(".ai-context/config.yaml")


def test_analyze_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a dummy file to analyze
        with open("test.py", "w") as f:
            f.write("def hello():\n")
            f.write("    print('hello')\n")

        result = runner.invoke(cli, ["analyze"])
        assert result.exit_code == 0


def test_profiles_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["profiles"])
    assert result.exit_code == 0
    assert "generic" in result.output
    assert "qgis" in result.output
