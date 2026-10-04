import hashlib

from ytc import studio


def test_approved_art_guard_rejects_post_review_replacements(tmp_path, monkeypatch):
    folder = tmp_path / "ep065"
    (folder / "art").mkdir(parents=True)
    asset = folder / "art" / "dated-1907.jpg"
    asset.write_bytes(b"verified archival art")
    meta = {"topic": "Quebec Bridge", "approved_art_sha256": {
        "art/dated-1907.jpg": hashlib.sha256(asset.read_bytes()).hexdigest()}}
    original = [{"source": "file", "path": "art/dated-1907.jpg"}]
    rejected = []
    monkeypatch.setattr(studio, "reject", lambda _folder, reason: rejected.append(reason))

    assert studio._reject_visual_plan(folder, meta, original) is None
    replacement = [{"source": "url", "url": "https://example.org/bridge-from-1916.jpg"}]
    assert "outside the approved source set" in studio._reject_visual_plan(folder, meta, replacement)["reason"]
    asset.write_bytes(b"silently replaced")
    assert "hash changed" in studio._reject_visual_plan(folder, meta, original)["reason"]
    assert len(rejected) == 2
