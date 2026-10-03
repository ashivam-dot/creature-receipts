import json
from pathlib import Path

from ytc.captions import write_ass
from ytc.spec import Beat, CaptionStyle, ShortSpec, Visual
from ytc.tts import Word
from ytc.visuals import _cached, _file


def test_reconstruction_label_is_burned_in_for_its_beat(tmp_path):
    spec = ShortSpec.load(Path(__file__).resolve().parents[2] / "content/episodes/ep042/short.yaml")
    assert spec.beats[0].visual.label == "TENOCHTITLAN • 2023 RECONSTRUCTION"
    out = tmp_path / "captions.ass"
    write_ass(
        [Word("To", 0.08, 0.3, 0)], CaptionStyle(), out, 3.4, {},
        Path(__file__).resolve().parents[1] / "assets/fonts",
        visual_labels=[(0.08, 3.3, spec.beats[0].visual.label)],
    )
    ass = out.read_text()
    assert "Dialogue: 1,0:00:00.08,0:00:03.30,Provenance" in ass
    assert "TENOCHTITLAN • 2023 RECONSTRUCTION" in ass


def test_local_derivative_keeps_source_credit_in_manifest_asset(tmp_path):
    source = tmp_path / "portrait.jpg"
    source.write_bytes(b"image bytes")
    credit = {"source": "Wikimedia Commons derivative", "title": "1938 portrait",
              "license": "Public domain", "url": "https://commons.wikimedia.org/wiki/File:Portrait.jpg"}
    asset = _file("portrait.jpg", tmp_path / "beat00", tmp_path, credit)
    assert {key: asset.credit[key] for key in credit} == credit
    assert asset.credit["path"] == str(source)


def test_cached_local_derivative_uses_current_credit_and_source(tmp_path):
    source = tmp_path / "portrait.jpg"
    source.write_bytes(b"current image")
    out = tmp_path / "work" / "assets" / "beat00"
    out.parent.mkdir(parents=True)
    cached_image = out.with_suffix(".jpg")
    cached_image.write_bytes(source.read_bytes())
    credit = {"source": "Wikimedia Commons derivative", "title": "1938 portrait",
              "license": "Public domain", "url": "https://commons.wikimedia.org/wiki/File:Portrait.jpg"}
    beat = Beat(text="Test", visual=Visual(source="file", path="portrait.jpg", credit=credit))
    out.with_suffix(".json").write_text(json.dumps({
        "visual": beat.visual.model_dump(), "path": str(cached_image), "kind": "image",
        "credit": {"source": "local file", "path": "/obsolete/worktree/portrait.jpg"}, "key": None,
    }))
    asset = _cached(beat, out, tmp_path)
    assert asset is not None
    assert asset.credit == {**credit, "path": str(source)}
    source.write_bytes(b"changed image")
    assert _cached(beat, out, tmp_path) is None
