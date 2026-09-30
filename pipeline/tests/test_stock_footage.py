from pathlib import Path

from ytc import pick, sources, visuals


class _Resp:
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def test_pexels_keeps_the_smallest_sharp_rendition(monkeypatch):
    monkeypatch.setenv("PEXELS_API_KEY", "k")
    video = {"id": 7, "duration": 14, "image": "https://images.pexels.com/7.jpg", "url": "https://www.pexels.com/video/octopus-on-a-reef-7/",
             "user": {"name": "Ana"}, "video_files": [
                 {"file_type": "video/mp4", "width": 540, "height": 960, "link": "https://v/sd.mp4"},
                 {"file_type": "video/mp4", "width": 1080, "height": 1920, "link": "https://v/hd.mp4"},
                 {"file_type": "video/mp4", "width": 2160, "height": 3840, "link": "https://v/uhd.mp4"}]}
    short = {**video, "id": 8, "duration": 3}
    monkeypatch.setattr(sources, "_get", lambda *a, **k: _Resp({"videos": [video, short]}))
    found = sources.pexels_videos("Octopus")
    assert [c["key"] for c in found] == ["pexels:7"]
    assert found[0]["original"] == "https://v/hd.mp4" and found[0]["kind"] == "video"
    assert found[0]["title"] == "Octopus on a reef"


def test_no_key_no_search(monkeypatch):
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    monkeypatch.delenv("PIXABAY_API_KEY", raising=False)
    monkeypatch.setattr(sources, "_get", lambda *a, **k: (_ for _ in ()).throw(AssertionError("called")))
    assert sources.stock_videos("Octopus") == []


def test_landscape_needs_1080_tall():
    assert not sources._clip_ok(1280, 720)
    assert sources._clip_ok(1920, 1080)
    assert sources._clip_ok(720, 1280)


def test_footage_becomes_a_still_camera_video_visual():
    candidate = {"key": "pexels:7", "origin": "pexels", "kind": "video", "title": "Octopus", "original": "https://v/hd.mp4",
                 "width": 1080, "height": 1920, "duration": 14, "license": "Pexels License", "artist": "Ana",
                 "page": "https://www.pexels.com/video/7/", "source_name": "Pexels"}
    visual = pick.picture_visual(candidate, 2, "zoom_in")
    assert visual["url"] == "https://v/hd.mp4" and visual["motion"] == "none"
    assert visual["_choice"]["kind"] == "video" and visual["credit"]["source"] == "Pexels"


def test_url_visual_with_a_video_suffix_downloads_as_video(monkeypatch, tmp_path):
    from ytc.spec import Beat

    monkeypatch.setattr(visuals, "_download", lambda url, path: (path.write_bytes(b"x"), path)[1])
    beat = Beat.model_validate({"text": "An octopus.", "visual": {"source": "url", "url": "https://v/hd.mp4?x=1",
                                                                  "credit": {"source": "Pexels", "url": "https://p/7"}}})
    asset = visuals._url(beat, tmp_path / "beat00")
    assert asset.kind == "video" and Path(asset.path).suffix == ".mp4"
