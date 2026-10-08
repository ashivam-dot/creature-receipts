"""Owner-run: put channel 2's Buffer API key and Cloudinary URL into the Modal secret the Atlas runs read.

    MODAL_PROFILE=aksha-shivam18 pipeline/.venv/bin/python kit/atlas_keys.py

Both values are typed hidden, checked against Buffer and Cloudinary, and go straight into the Modal secret
`creature-receipts-studio`; nothing is printed or written to disk. Where to find them (Chrome Profile 5):
  Buffer:     publish.buffer.com > Settings > API (create a key if none is shown)
  Cloudinary: console.cloudinary.com > Dashboard > "API environment variable" (cloudinary://...)
"""

import getpass
import sys
import urllib.parse

import modal
import requests

SECRET = "creature-receipts-studio"
WORKSPACE = "aksha-shivam18"
BUFFER_CHANNEL = "6abcba6dea19ca0bde30177e"


def _buffer(key: str, query: str, variables: dict | None = None) -> dict:
    response = requests.post("https://api.buffer.com", json={"query": query, "variables": variables or {}},
                             headers={"Authorization": f"Bearer {key}"}, timeout=60)
    if not response.ok or response.json().get("errors"):
        sys.exit(f"Buffer refused that key (HTTP {response.status_code}).")
    return response.json()["data"]


def main() -> None:
    if modal.Workspace.from_context().hydrate().name != WORKSPACE:
        sys.exit(f"Run this with MODAL_PROFILE={WORKSPACE}.")
    key = getpass.getpass("Buffer API key (hidden): ").strip()
    orgs = _buffer(key, "query { account { organizations { id name } } }")["account"]["organizations"]
    org = None
    for candidate in orgs:
        found = _buffer(key, "query C($input: ChannelsInput!) { channels(input: $input) { id service } }",
                        {"input": {"organizationId": candidate["id"]}})["channels"]
        if any(c["id"] == BUFFER_CHANNEL for c in found):
            org = candidate
    if org is None:
        sys.exit("That Buffer account doesn't have channel 2's YouTube channel; use aksha.shivam18's Buffer.")
    url = getpass.getpass("Cloudinary URL, cloudinary://... (hidden): ").strip()
    parts = urllib.parse.urlparse(url)
    if parts.scheme != "cloudinary" or not (parts.hostname and parts.username and parts.password):
        sys.exit("That isn't a cloudinary://KEY:SECRET@CLOUD URL.")
    ping = requests.get(f"https://api.cloudinary.com/v1_1/{parts.hostname}/usage", timeout=60,
                        auth=(urllib.parse.unquote(parts.username), urllib.parse.unquote(parts.password)))
    if not ping.ok:
        sys.exit(f"Cloudinary refused that URL (HTTP {ping.status_code}).")
    modal.Secret.from_name(SECRET).update({"BUFFER_API_KEY": key, "BUFFER_ORG_ID": org["id"],
                                           "BUFFER_YOUTUBE_CHANNEL_ID": BUFFER_CHANNEL, "CLOUDINARY_URL": url})
    print(f"Saved to the Modal secret {SECRET}. Buffer organization: {org['name']}. Cloudinary cloud: {parts.hostname}.")


if __name__ == "__main__":
    main()
