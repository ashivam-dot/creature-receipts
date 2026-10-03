import json

from ytc import auto, youtube


def test_withdrawn_sent_video_is_excluded_from_live_checks_and_learning(tmp_path, monkeypatch):
    folder = tmp_path / "ep025"
    folder.mkdir()
    (folder / "short.yaml").write_text("id: ep025\ntitle: R101\nseries: The Last Hours\n")
    (folder / "publish.json").write_text(json.dumps({
        "id": "ep025", "status": "sent", "sent_at": "2026-10-03T00:00:00+00:00",
        "youtube_url": "https://www.youtube.com/shorts/qtmFWWw0npA"}))
    (folder / "withdrawal.json").write_text(json.dumps({
        "reason": "incorrect survival claim", "youtube_video_id": "qtmFWWw0npA"}))
    monkeypatch.setattr(auto, "EPISODES", tmp_path)
    monkeypatch.setattr(youtube, "_credentials", lambda: (_ for _ in ()).throw(AssertionError("API must not be called")))

    episode = auto.episodes()[0]
    assert episode["state"] == "withdrawn"
    assert auto.inventory([episode])["total"] == 0
    assert youtube.check_live(tmp_path) == []
    assert youtube.fix_languages(tmp_path) == []
