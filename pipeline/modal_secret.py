"""Set up, from the Mac, what the studio's runs on Modal (cloud.studio_run) sign in with. Prints no secret values.

1. A deploy key that can push to ashivam-dot/creature-receipts and nothing else (secrets/modal_deploy_key, git-ignored).
2. An ntfy topic for alerts on the owner's phone (YTC_NTFY_TOPIC in pipeline/.env and a GitHub secret).
3. The Modal secret `creature-receipts-studio`: draft-production keys and the deploy key.

    python3 pipeline/modal_secret.py setup    # deploy key and ntfy topic only
    python3 pipeline/modal_secret.py modal    # explicitly rebuild the Modal secret after reviewing the key list
"""

import json
import os
import secrets as tokens
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "pipeline" / ".env"
KEY = ROOT / "secrets" / "modal_deploy_key"
REPO = "ashivam-dot/creature-receipts"
SECRET = "creature-receipts-studio"
FROM_ENV = ("YTC_CONTACT", "YTC_GEMINI_API_KEY",
            "YTC_MISTRAL_API_KEY", "YTC_OPENROUTER_API_KEY", "YTC_CURSOR_API_KEY", "YTC_NTFY_TOPIC",
            "PEXELS_API_KEY", "PIXABAY_API_KEY")
# Modal's monthly credit (auto.MODAL_CREDIT) when YTC_MODAL_CREDIT isn't in pipeline/.env: the Starter plan's $1.
# With a card on file it's $30; set YTC_MODAL_CREDIT=30 then.
MODAL_CREDIT = "1"


def env_values() -> dict:
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("'\"")
    return values


def run(*args: str, **kw) -> str:
    done = subprocess.run(list(args), capture_output=True, text=True, **kw)
    if done.returncode:
        raise SystemExit(f"{' '.join(args[:3])} failed: {done.stderr.strip()[:400]}")
    return done.stdout


def deploy_key() -> None:
    if not KEY.exists():
        KEY.parent.mkdir(exist_ok=True)
        run("ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "creature-receipts studio on Modal", "-f", str(KEY))
        print("made the deploy key")
    if "Modal studio runs" not in run("gh", "repo", "deploy-key", "list", "--repo", REPO):
        run("gh", "repo", "deploy-key", "add", str(KEY.with_suffix(".pub")), "--repo", REPO, "--allow-write",
            "--title", "Modal studio runs")
        print("added it to the repository, with write access")


def ntfy_topic() -> None:
    if not env_values().get("YTC_NTFY_TOPIC"):
        topic = "yt-" + "".join(c for c in tokens.token_urlsafe(16) if c.isalnum())[:14].lower()
        with ENV.open("a", encoding="utf-8") as fh:
            fh.write(f"\n# The owner's phone subscribes to this ntfy topic for alerts (monitor/monitor.py).\nYTC_NTFY_TOPIC={topic}\n")
        print("made an ntfy topic, on the YTC_NTFY_TOPIC line of pipeline/.env")
    subprocess.run(["gh", "secret", "set", "YTC_NTFY_TOPIC", "--repo", REPO], input=env_values()["YTC_NTFY_TOPIC"],
                   text=True, check=True, capture_output=True)
    print("set the YTC_NTFY_TOPIC secret on GitHub")


def modal_secret() -> None:
    values = env_values()
    payload = {k: values[k] for k in FROM_ENV if values.get(k)}
    payload |= {"YTC_MODAL_CREDIT": values.get("YTC_MODAL_CREDIT") or MODAL_CREDIT,
                "YTC_DEPLOY_KEY": KEY.read_text(encoding="utf-8")}
    env = {k: v for k, v in os.environ.items() if not (
        k.startswith("BUFFER_") or k in ("CLOUDINARY_URL", "YTC_GOOGLE_CLIENT", "YTC_GOOGLE_TOKEN",
                                       "YTC_AUTONOMOUS_RELEASE"))}
    env.update({k: v for k, v in values.items() if k.startswith("MODAL_")})
    fd, path = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        run("uv", "run", "--no-sync", "modal", "secret", "create", SECRET, "--from-json", path, "--force",
            cwd=ROOT / "pipeline", env=env)
    finally:
        os.remove(path)
    missing = [k for k in FROM_ENV if k not in payload]
    print(f"Modal secret {SECRET}: {', '.join(sorted(payload))}" + (f" (missing: {', '.join(missing)})" if missing else ""))


def main(argv: list[str] | None = None) -> None:
    command = sys.argv[1:] if argv is None else argv
    if command == ["setup"]:
        deploy_key()
        ntfy_topic()
        print("To rebuild the draft-only Modal secret, run: python3 pipeline/modal_secret.py modal")
    elif command == ["modal"]:
        modal_secret()
    else:
        raise SystemExit("usage: python3 pipeline/modal_secret.py {setup|modal}")


if __name__ == "__main__":
    main()
