from ytc import sources


def test_only_named_open_licenses_count():
    assert sources._license_ok("Public domain", 1930)
    assert sources._license_ok("CC BY 2.0", None)
    assert not sources._license_ok("No restrictions", 1925)
    assert not sources._license_ok("No known copyright restrictions", 1900)
