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


def test_pinned_story_rewrite_keeps_each_visual_event_mapping():
    before = {"beats": [
        {"claims": [12, 13], "year": 1907, "subjects": ["Quebec Bridge"]},
        {"claims": [15, 13], "year": 1907, "subjects": ["Quebec Bridge"]},
    ]}
    after = {"beats": [
        {"claims": [13], "year": 1907, "subjects": ["Quebec Bridge"]},
        {"claims": [17, 15, 13], "year": 1907, "subjects": ["Quebec Bridge"]},
    ]}
    assert studio._pinned_rewrite_problem(before, after) is None
    assert "beat count" in studio._pinned_rewrite_problem(before, {"beats": after["beats"][:1]})
    changed = {"beats": [dict(after["beats"][0], claims=[14]), after["beats"][1]]}
    assert "beat 1" in studio._pinned_rewrite_problem(before, changed)
    changed = {"beats": [dict(after["beats"][0], year=1916), after["beats"][1]]}
    assert "year" in studio._pinned_rewrite_problem(before, changed)
    changed = {"beats": [dict(after["beats"][0], subjects=["Other bridge"]), after["beats"][1]]}
    assert "subject" in studio._pinned_rewrite_problem(before, changed)
