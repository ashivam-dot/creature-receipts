from ytc.check import minor_differences

EP068 = ["'a' heard as '(nothing)'",
         "'s' heard as '(nothing)' after 'flew over beijing'",
         "'a' heard as '(nothing)' after 'of the capital'",
         "base.en: 'ton' heard as 'tonne' after 'a 3'",
         "base.en: 's' heard as '(nothing)' after 'flew over beijing'",
         "base.en: 'wanggongchang' heard as 'wangongchang' after '1626 the imperial'"]


def test_dropped_short_words_and_respellings_are_recognizer_noise():
    assert minor_differences(EP068)
    assert minor_differences(["'route' heard as 'root'", "'(nothing)' heard as 'his'"])


def test_numbers_and_changed_words_are_never_noise():
    assert not minor_differences(["'1871' heard as '1817'"])
    assert not minor_differences(["'fire' heard as 'flood'", "'killed' heard as 'filled'",
                                  "'north' heard as 'south'"])
    assert not minor_differences([])
    assert not minor_differences(["'a' heard as '(nothing)'"] * 9)
