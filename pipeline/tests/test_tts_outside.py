from ytc import tts


def test_speech_before_the_script_is_found_and_a_breath_is_not():
    words = [tts.Word("This", 13.5, 13.8, 0), tts.Word("fish", 13.9, 14.1, 0)]
    heard = [(" Read", 0.0, 0.3), (" the", 0.3, 0.4), (" transcript", 0.4, 1.0), (" This", 13.5, 13.8),
             (" fish", 13.9, 14.1), (" Oh", 14.4, 14.6)]
    assert tts._outside(words, heard) == (17, 0)


def test_a_clean_take_has_nothing_outside():
    words = [tts.Word("This", 0.1, 0.4, 0), tts.Word("fish", 0.5, 0.8, 0)]
    assert tts._outside(words, [(" This", 0.1, 0.4), (" fish", 0.5, 0.8)]) == (0, 0)


def test_overrides_are_read_as_the_plain_word():
    assert tts._OVERRIDE.sub(r"\1", "Pope [Formosus](/fɔɹmˈOsəs/) was tried") == "Pope Formosus was tried"
