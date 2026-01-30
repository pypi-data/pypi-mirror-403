from click.testing import CliRunner
from jcgraph.cli.main import app

def test_version():
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
