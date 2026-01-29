from pprint import pp

from typer.testing import CliRunner

from s3cd import cli


class TestCli(object):
    def test_version(self, runner: CliRunner):
        result = runner.invoke(cli, ['--version'])
        pp(result.output)
        assert result.exit_code == 0
