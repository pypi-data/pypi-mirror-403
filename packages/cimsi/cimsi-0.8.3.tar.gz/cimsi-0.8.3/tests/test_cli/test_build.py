import pytest
from click.testing import CliRunner
from imsi.cli.entry import cli
from pathlib import Path
import subprocess
import shutil
import os
import yaml
from imsi import __version__


from imsi.user_interface.setup_manager import InvalidSetupConfig


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def local_test_dir(request):
    """Create a temporary test directory under the current working directory and clean up after."""
    tmp_dir = Path.cwd() / f"test_tmp_{request.node.name}"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True)
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.mark.parametrize(
    ("ctx_args", "before_args", "delimiter", "after_args"),
    [
        ("-f", None, None, "-c"),
        (None, "-c", '--', "-h"),
        ("-f", "-c", '--', '-c'),
    ]
)
def test_build_fails_when_args_malformed_with_eoo_delimiter(
        runner, local_test_dir,
        ctx_args, before_args, delimiter, after_args
        ):
    cwd_before = os.getcwd()
    os.chdir(local_test_dir)

    build_args = [ctx_args, "build", before_args, delimiter, after_args]
    build_args = [x for x in build_args if x is not None]
    try:
        result = runner.invoke(cli, build_args)
    finally:
        os.chdir(cwd_before)
    assert result.exit_code != 0
