"""Publisher-side acceptance verification: intentionally standard-library only."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
VERSION = 1

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(folder: Path, media_sha: str) -> dict:
    """Publisher validates the receipt and every bound artifact before accepting bytes."""
    qa = json.loads((folder / "qa.json").read_text())
    if qa.get("version") != VERSION or qa.get("passed") is not True or qa.get("media_sha256") != media_sha:
        raise ValueError("missing or invalid media quality receipt")
    for name, field in (("atlas.yaml", "script_sha256"), ("data.json", "data_sha256"), ("claims.json", "claims_sha256")):
        if digest(folder / name) != qa.get(field):
            raise ValueError(f"quality receipt does not bind {name}")
    claims = json.loads((folder / "claims.json").read_text())
    if claims["review"]["errors"] or claims["script_sha256"] != qa["script_sha256"] or claims["data_sha256"] != qa["data_sha256"]:
        raise ValueError("factual acceptance receipt is invalid")
    return qa
