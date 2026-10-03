from pathlib import Path

from ytc.captions import write_ass
from ytc.spec import CaptionStyle, ShortSpec
from ytc.tts import Word


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
