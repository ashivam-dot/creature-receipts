#!/usr/bin/env python3
"""Put a key into pipeline/.env without it passing through the chat or the terminal.

    python3 kit/setkey.py YTC_GEMINI_API_KEY         # the value is on the clipboard: copied in the browser
    python3 kit/setkey.py --modal                   # MODAL_TOKEN_ID and _SECRET from ~/.modal.toml
    python3 kit/setkey.py --google-client ~/Downloads/client_secret_....json
    python3 kit/setkey.py --set YTC_MODAL_CREDIT=30  # settings that aren't secret
    python3 kit/setkey.py --list                    # which names are set (never the values)

A key read from the clipboard is checked against the shape that service's keys have, written to
pipeline/.env (readable only by this user), and then the clipboard is cleared. Only the name and the
value's length are printed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "pipeline" / ".env"
EXAMPLE = ROOT / "pipeline" / ".env.example"
SECRETS = ROOT / "secrets"

# What each service's keys look like, to catch copying the wrong thing (a URL, a label, half a key).
SHAPES = {
    "YTC_GEMINI_API_KEY": r"AIza[0-9A-Za-z_-]{35}|AQ\.[0-9A-Za-z_-]{30,}",
    "MODAL_TOKEN_ID": r"ak-[A-Za-z0-9]+",
    "MODAL_TOKEN_SECRET": r"as-[A-Za-z0-9]+",
    "YTC_MISTRAL_API_KEY": r"[A-Za-z0-9]{24,64}",
    "YTC_OPENROUTER_API_KEY": r"sk-or-[A-Za-z0-9-]{20,}",
    "YTC_CURSOR_API_KEY": r"\S{20,}",
    "PEXELS_API_KEY": r"\S{20,}",
    "PIXABAY_API_KEY": r"\S{20,}",
    "CLOUDFLARE_API_TOKEN": r"\S{20,}",
}
REQUIRED = ("YTC_CONTACT", "MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET", "YTC_GEMINI_API_KEY")
OPTIONAL = ("YTC_MODAL_CREDIT", "YTC_NTFY_TOPIC", "YTC_MISTRAL_API_KEY", "YTC_OPENROUTER_API_KEY", "YTC_CURSOR_API_KEY",
            "PEXELS_API_KEY", "PIXABAY_API_KEY")
NAME = re.compile(r"[A-Z][A-Z0-9_]{2,60}")


def env_lines() -> list[str]:
    if not ENV.exists():
        ENV.parent.mkdir(parents=True, exist_ok=True)
        ENV.write_text(EXAMPLE.read_text(encoding="utf-8") if EXAMPLE.exists() else "", encoding="utf-8")
        os.chmod(ENV, 0o600)
    return ENV.read_text(encoding="utf-8").splitlines()


def env_values() -> dict[str, str]:
    values = {}
    for line in env_lines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("'\"")
    return values


def write_value(name: str, value: str) -> None:
    """Replace NAME's line (or its commented-out example) in pipeline/.env, or add one."""
    lines = env_lines()
    pattern = re.compile(rf"^\s*#?\s*{re.escape(name)}=")
    entry = f"{name}={value}"
    live = [i for i, line in enumerate(lines) if pattern.match(line) and not line.lstrip().startswith("#")]
    commented = [i for i, line in enumerate(lines) if pattern.match(line) and line.lstrip().startswith("#")]
    if live:
        lines[live[0]] = entry
        for i in reversed(live[1:]):
            del lines[i]
    elif commented:
        lines[commented[0]] = entry
    else:
        lines.append(entry)
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(ENV, 0o600)


def clipboard() -> str:
    if (test := os.environ.get("SETKEY_TEST_CLIPBOARD")) is not None:
        return test
    return subprocess.run(["pbpaste"], capture_output=True, text=True, check=True).stdout


def clear_clipboard() -> None:
    if os.environ.get("SETKEY_TEST_CLIPBOARD") is None:
        subprocess.run(["pbcopy"], input="", text=True, check=False)


def set_from_clipboard(name: str, force: bool) -> None:
    value = clipboard().strip()
    if value.startswith(f"{name}="):
        value = value[len(name) + 1:].strip()
    value = value.strip("'\"")
    if not value:
        raise SystemExit("setkey: the clipboard is empty; copy the key in the browser first")
    if any(c.isspace() for c in value):
        raise SystemExit("setkey: the clipboard has spaces or line breaks in it, so it isn't just the key; copy only the key")
    shape = SHAPES.get(name)
    if shape and not re.fullmatch(shape, value) and not force:
        raise SystemExit(f"setkey: that doesn't look like a {name} ({len(value)} characters); nothing saved. "
                         "Copy it again, or add --force if you're sure")
    write_value(name, value)
    clear_clipboard()
    print(f"{name} saved to pipeline/.env ({len(value)} characters); clipboard cleared")


def modal_profiles(text: str) -> list[dict]:
    """The profiles in ~/.modal.toml: [name] sections of key = value lines (tomllib needs Python 3.11)."""
    profiles: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            profiles.append({"_name": line[1:-1].strip()})
        elif "=" in line and profiles and not line.startswith("#"):
            key, value = (part.strip() for part in line.split("=", 1))
            value = value.strip("'\"")
            profiles[-1][key] = value.lower() == "true" if value.lower() in ("true", "false") else value
    return profiles


def set_modal(profile: str | None = None) -> None:
    """The named profile's token, or the active one's: each channel can have its own Modal workspace."""
    config = Path.home() / ".modal.toml"
    if not config.exists():
        raise SystemExit("setkey: ~/.modal.toml is missing; run `uv run --no-sync modal token new` in pipeline/ first")
    profiles = modal_profiles(config.read_text(encoding="utf-8"))
    if profile:
        chosen = next((p for p in profiles if p["_name"] == profile), None)
        if not chosen:
            raise SystemExit(f"setkey: no Modal profile {profile!r} in ~/.modal.toml")
    else:
        chosen = next((p for p in profiles if p.get("active") is True), None)
        chosen = chosen or next((p for p in profiles if p.get("token_id")), None)
    if not chosen or not chosen.get("token_id") or not chosen.get("token_secret"):
        raise SystemExit("setkey: no Modal token in ~/.modal.toml; run `uv run --no-sync modal token new` again")
    write_value("MODAL_TOKEN_ID", chosen["token_id"])
    write_value("MODAL_TOKEN_SECRET", chosen["token_secret"])
    print("MODAL_TOKEN_ID and MODAL_TOKEN_SECRET saved to pipeline/.env")


def set_google_client(path: Path) -> None:
    data = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if "installed" not in data:
        raise SystemExit("setkey: that file isn't a Desktop app client (it has no 'installed' section); "
                         "create the OAuth client with type 'Desktop app'")
    SECRETS.mkdir(mode=0o700, exist_ok=True)
    target = SECRETS / "client_secret.json"
    shutil.copyfile(path.expanduser(), target)
    os.chmod(target, 0o600)
    print("saved secrets/client_secret.json; you can delete the download")


def set_plain(pair: str) -> None:
    if "=" not in pair:
        raise SystemExit("setkey: --set takes NAME=value")
    name, value = pair.split("=", 1)
    name, value = name.strip(), value.strip()
    if not NAME.fullmatch(name):
        raise SystemExit(f"setkey: {name!r} isn't a variable name")
    if name in SHAPES:
        raise SystemExit(f"setkey: {name} is a secret; copy it and run `python3 kit/setkey.py {name}` instead")
    write_value(name, value)
    print(f"{name}={value} saved to pipeline/.env")


def show() -> None:
    values = env_values()
    for group, names in (("required", REQUIRED), ("optional", OPTIONAL)):
        for name in names:
            print(f"{'set    ' if values.get(name) else 'MISSING' if group == 'required' else 'not set'}  {name}  ({group})")
    for name, label in (("client_secret.json", "the OAuth client (ACCOUNTS.md, step 3)"), ("token.json", "YouTube's sign-in (`ytc auth`)")):
        print(f"{'set    ' if (SECRETS / name).exists() else 'MISSING'}  secrets/{name}  {label}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("name", nargs="?", help="the variable to set from the clipboard")
    parser.add_argument("--force", action="store_true", help="save it even if it doesn't look like that service's keys")
    parser.add_argument("--modal", action="store_true", help="copy the Modal token from ~/.modal.toml")
    parser.add_argument("--modal-profile", help="with --modal: the ~/.modal.toml profile to copy (default: the active one)")
    parser.add_argument("--google-client", type=Path, help="the downloaded OAuth client JSON")
    parser.add_argument("--set", dest="plain", help="NAME=value for a setting that isn't secret")
    parser.add_argument("--list", action="store_true", help="show which names are set")
    args = parser.parse_args()
    if args.list:
        show()
    elif args.modal:
        set_modal(args.modal_profile)
    elif args.google_client:
        set_google_client(args.google_client)
    elif args.plain:
        set_plain(args.plain)
    elif args.name:
        if not NAME.fullmatch(args.name):
            raise SystemExit(f"setkey: {args.name!r} isn't a variable name")
        set_from_clipboard(args.name, args.force)
    else:
        parser.print_help()


if __name__ == "__main__":
    sys.exit(main())
