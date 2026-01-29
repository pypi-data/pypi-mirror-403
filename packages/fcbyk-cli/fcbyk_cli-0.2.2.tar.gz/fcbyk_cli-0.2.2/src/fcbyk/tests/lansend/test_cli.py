import importlib


def test_lansend_help():
    from click.testing import CliRunner
    from fcbyk.cli import cli

    r = CliRunner().invoke(cli, ["lansend", "--help"])
    assert r.exit_code == 0
