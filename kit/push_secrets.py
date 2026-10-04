#!/usr/bin/env python3
"""Copy draft-production keys into the producer repository's Actions secrets and variables.
Values go to `gh` on stdin; only names are printed. Publisher keys belong to the separate control repository.

    python3 kit/push_secrets.py            # the repository in kit/channel.json
    python3 kit/push_secrets.py --dry-run  # list what would be set

Run it again after changing a draft key. Rebuild Modal's copy separately with
`python3 pipeline/modal_secret.py modal` after reviewing the key list.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "pipeline" / ".env"
# The secrets .github/workflows/*.yml read. YTC_NTFY_TOPIC is also set by pipeline/modal_secret.py.
FROM_ENV = ("YTC_CONTACT", "MODAL_TOKEN_ID",
            "MODAL_TOKEN_SECRET", "YTC_GEMINI_API_KEY", "YTC_MISTRAL_API_KEY", "YTC_OPENROUTER_API_KEY",
            "YTC_CURSOR_API_KEY", "YTC_NTFY_TOPIC",
            "PEXELS_API_KEY", "PIXABAY_API_KEY")
# Actions variables (not secret). YTC_MODAL_CREDIT tells the backup how much Modal credit the month has.
VARIABLES = {"YTC_MODAL_CREDIT": "1", "YTC_LLM_FIRST": None, "YTC_CURSOR_MODEL": None}


def env_values() -> dict[str, str]:
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("'\"")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", help="owner/repository (default: kit/channel.json)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    repo = args.repo or json.loads((ROOT / "kit" / "channel.json").read_text(encoding="utf-8"))["repo"]
    values = env_values()
    secrets = {name: values[name] for name in FROM_ENV if values.get(name)}
    variables = {name: values.get(name) or default for name, default in VARIABLES.items() if values.get(name) or default}
    missing = [n for n in FROM_ENV if n not in secrets]

    for name, value in secrets.items():
        if not args.dry_run:
            done = subprocess.run(["gh", "secret", "set", name, "--repo", repo], input=value, text=True, capture_output=True)
            if done.returncode:
                raise SystemExit(f"push_secrets: setting {name} failed: {done.stderr.strip()[:300]}")
    for name, value in variables.items():
        if not args.dry_run:
            done = subprocess.run(["gh", "variable", "set", name, "--repo", repo, "--body", value], text=True, capture_output=True)
            if done.returncode:
                raise SystemExit(f"push_secrets: setting variable {name} failed: {done.stderr.strip()[:300]}")
    verb = "would set" if args.dry_run else "set"
    print(f"{verb} secrets on {repo}: {', '.join(sorted(secrets)) or 'none'}")
    print(f"{verb} variables: {', '.join(f'{k}={v}' for k, v in sorted(variables.items())) or 'none'}")
    if missing:
        print(f"not set (not in pipeline/.env yet): {', '.join(missing)}")


if __name__ == "__main__":
    sys.exit(main())
