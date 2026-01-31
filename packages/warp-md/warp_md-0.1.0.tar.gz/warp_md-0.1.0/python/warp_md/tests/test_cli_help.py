import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PYTHON_SRC = str(ROOT / "python")


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = PYTHON_SRC + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "warp_md.cli", *args],
        capture_output=True,
        text=True,
        env=env,
    )


def test_list_plans_help() -> None:
    result = _run("list-plans")
    assert result.returncode == 0


def test_rg_help() -> None:
    result = _run("rg", "--help")
    assert result.returncode == 0


def test_example() -> None:
    result = _run("example")
    assert result.returncode == 0
