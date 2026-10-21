"""The publisher runs the title check without numpy or PIL (history-last-hours-control atlas-publish.yml), so the
check must import without them (b3 re-check, 2026-10-22)."""
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"


def test_the_title_check_imports_without_numpy_or_pil():
    code = ("import sys; sys.modules['numpy'] = None; sys.modules['PIL'] = None\n"
            "from ytc.atlas import publish\n"
            "from ytc.atlas.writer import episode_title_lint, title_lint\n"
            "title_lint('Places Ranked by Megacity Populations')\n"
            "print('ok')")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env={"PYTHONPATH": str(SRC)})
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "ok"
