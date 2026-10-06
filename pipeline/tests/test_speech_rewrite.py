from ytc import studio


def test_misheard_reads_each_script_word_once_from_both_recognizers():
    result = {"speech": {"differences": [
        "'pharaoh djer' heard as 'farogirr' after 'were entombed around'",
        "'abydos' heard as 'abidos' after 'qa ab near'",
        "base.en: 'abydos' heard as 'abidos' after 'qa ab near'",
        "base.en: 'perimortem' heard as 'paramordum' after 'skulls revealed fatal'",
    ]}}
    assert studio._misheard(result) == ["pharaoh djer", "abydos", "perimortem"]
    assert studio._misheard({"speech": {"error": "recognizer failed"}}) == []
