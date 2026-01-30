# tests/test_starter_demo.py
import subprocess
import shutil
from pathlib import Path


def run(cmd, cwd=None):
    """Run a shell command and stream output live."""
    subprocess.run(
        cmd,
        cwd=cwd,
        shell=True,
        check=True,
        stdout=None,   # inherit terminal stdout
        stderr=None,   # inherit terminal stderr
    )

def test_triggerflow_starter_demo():
    project_dir = Path("test_demo")

    try:
    # triggerflow new test_demo
        run("triggerflow new test_demo")

        # kedro run
        run("kedro run", cwd=project_dir)

    finally:
        # cleanup (always)
        if project_dir.exists():
            shutil.rmtree(project_dir)
