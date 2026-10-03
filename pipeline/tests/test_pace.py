from ytc import auto


def _setup(monkeypatch, day, engaged, share=None):
    monkeypatch.setattr(auto, "day_number", lambda today=None: day)
    monkeypatch.setattr(auto, "_pace_numbers", lambda: (engaged, share or [0.6] * len(engaged)))


def test_relaunch_starts_at_one_reviewed_short_per_day(monkeypatch):
    _setup(monkeypatch, 3, [])
    assert auto.slots_per_day() == 1
    _setup(monkeypatch, -1, [])
    assert auto.slots_per_day() == 1


def test_no_volume_increase_from_too_few_shorts_or_views(monkeypatch):
    _setup(monkeypatch, 55, [1000.0] * 12)
    assert auto.slots_per_day() == 1
    _setup(monkeypatch, 55, [4.0] * 20)
    assert auto.slots_per_day() == 1


def test_stable_engagement_earns_only_planned_pace(monkeypatch):
    _setup(monkeypatch, 20, [1000.0] * 20)
    assert auto.slots_per_day() == 2
    _setup(monkeypatch, 35, [1000.0] * 10 + [1200.0] * 10)
    assert auto.slots_per_day() == 3


def test_mild_slip_caps_pace_at_two_and_large_drop_returns_to_one(monkeypatch):
    _setup(monkeypatch, 55, [1000.0] * 10 + [850.0] * 10)
    assert auto.slots_per_day() == 2
    _setup(monkeypatch, 55, [1000.0] * 10 + [600.0] * 10)
    assert auto.slots_per_day() == 1


def test_unreadable_numbers_keep_pilot_pace(monkeypatch):
    monkeypatch.setattr(auto, "day_number", lambda today=None: 40)

    def broken():
        raise ValueError("bad file")

    monkeypatch.setattr(auto, "_pace_numbers", broken)
    assert auto.slots_per_day() == 1
