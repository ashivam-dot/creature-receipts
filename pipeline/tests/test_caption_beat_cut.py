from pathlib import Path

from ytc.captions import write_ass, write_srt
from ytc.spec import CaptionStyle
from ytc.tts import Word


FONTS = Path(__file__).resolve().parents[1] / "assets" / "fonts"


def test_last_caption_stops_at_picture_cut_even_when_word_tail_is_late(tmp_path):
    # A real pilot left "27" over the next report card because the aligner
    # extended its last word into the next beat's first word.
    words = [Word("August", 0.70, 0.80, 0), Word("27.", 0.80, 1.30, 0),
             Word("But", 1.125, 1.30, 1)]
    ass = tmp_path / "captions.ass"
    srt = tmp_path / "captions.srt"
    cuts = {0: 1.0, 1: 2.0}

    write_ass(words, CaptionStyle(), ass, 2.0, {}, FONTS, beat_ends=cuts)
    write_srt(words, srt, beat_ends=cuts)

    older = [line for line in ass.read_text().splitlines()
             if line.startswith("Dialogue: 0") and ("AUGUST" in line or "27" in line)]
    assert older
    assert all(line.split(",", 3)[2] <= "0:00:01.00" for line in older)
    assert "00:00:00,700 --> 00:00:01,000" in srt.read_text()
    assert "00:00:00,700 --> 00:00:01,300" not in srt.read_text()


def test_source_label_preserves_finding_number_punctuation(tmp_path):
    ass = tmp_path / "captions.ass"
    write_ass([Word("Finding", 0.1, 0.5, 0)], CaptionStyle(), ass, 1.0, {}, FONTS,
              visual_labels=[(0, 1, "1908 Royal Commission · finding (A)")])
    assert "1908 ROYAL COMMISSION · FINDING (A)" in ass.read_text()
