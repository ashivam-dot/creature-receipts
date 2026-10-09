import json

from ytc.atlas import pipeline, stats


def test_hold_renders_nothing(tmp_path, monkeypatch):
    hold = tmp_path / "atlas_hold.json"
    hold.write_text(json.dumps({"reason": "format rework"}))
    monkeypatch.setattr(pipeline, "HOLD", hold)
    monkeypatch.setattr(pipeline, "sync", lambda: ["atlas001"])
    monkeypatch.setattr(stats, "update", lambda episodes, root: {"atlas001": {}})
    monkeypatch.setattr(pipeline, "make_next", lambda: (_ for _ in ()).throw(AssertionError("rendered while held")))

    result = pipeline.run()

    assert result == {"outcome": "held", "reason": "format rework", "synced": ["atlas001"], "tracked": 1}
