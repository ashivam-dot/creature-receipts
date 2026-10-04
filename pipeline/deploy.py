"""Deploy the Modal app from the Mac with pipeline/.env loaded, as the studio's own runs do with their secret.

    python3 pipeline/deploy.py

A bare `modal deploy` reads no .env, and cloud.studio_secret is built from the deploying environment.
"""
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
env = {k: v for k, v in os.environ.items() if not (
    k.startswith("BUFFER_") or k in ("CLOUDINARY_URL", "YTC_GOOGLE_CLIENT", "YTC_GOOGLE_TOKEN",
                                           "YTC_AUTONOMOUS_RELEASE"))}
for line in (HERE / ".env").read_text(encoding="utf-8").splitlines():
    name, sep, value = line.partition("=")
    if sep and name.strip() and not name.lstrip().startswith("#") and name.strip() in (
        "YTC_CONTACT", "YTC_GEMINI_API_KEY", "YTC_MISTRAL_API_KEY", "YTC_OPENROUTER_API_KEY",
        "YTC_CURSOR_API_KEY", "YTC_CURSOR_MODEL", "YTC_LLM_FIRST", "PEXELS_API_KEY", "PIXABAY_API_KEY",
        "MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET",
    ):
        env.setdefault(name.strip(), value.strip().strip('"').strip("'"))
subprocess.run(["uv", "run", "--no-sync", "modal", "deploy", "-m", "ytc.cloud"], cwd=HERE, env={**env, "PYTHONPATH": str(HERE / "src")},
               check=True)
