"""Deploy the Modal app from the Mac with pipeline/.env loaded, as the studio's own runs do with their secret.

    python3 pipeline/deploy.py

A bare `modal deploy` reads no .env, and cloud.studio_secret is built from the deploying environment, so it would
publish workers without their keys until the next studio run redeploys.
"""
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
env = dict(os.environ)
for line in (HERE / ".env").read_text(encoding="utf-8").splitlines():
    name, sep, value = line.partition("=")
    if sep and name.strip() and not name.lstrip().startswith("#"):
        env.setdefault(name.strip(), value.strip().strip('"').strip("'"))
subprocess.run(["uv", "run", "--no-sync", "modal", "deploy", "-m", "ytc.cloud"], cwd=HERE, env={**env, "PYTHONPATH": str(HERE / "src")},
               check=True)
