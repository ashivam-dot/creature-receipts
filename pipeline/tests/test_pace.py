from ytc import auto


def _setup(monkeypatch, day, engaged, share=None):
    monkeypatch.setattr(auto, "day_number", lambda today=None: day)
    monkeypatch.setattr(auto, "_pace_numbers", lambda: (engaged, share or [0.6] * len(engaged)))


def test_first_two_weeks_post_three_a_day(monkeypatch):
    _setup(monkeypatch, 3, [])
    assert auto.slots_per_day() == 3


def test_before_launch_posts_three(monkeypatch):
    _setup(monkeypatch, -1, [])
    assert auto.slots_per_day() == 3


def test_without_twenty_shorts_of_numbers_the_pace_stops_at_four(monkeypatch):
    _setup(monkeypatch, 55, [1000.0] * 12)
    assert auto.slots_per_day() == 4


def test_holding_numbers_earn_the_planned_pace(monkeypatch):
    _setup(monkeypatch, 20, [1000.0] * 10 + [1000.0] * 10)
    assert auto.slots_per_day() == 4
    _setup(monkeypatch, 35, [1000.0] * 10 + [1200.0] * 10)
    assert auto.slots_per_day() == 5


def test_slipping_views_per_short_hold_the_pace_at_four(monkeypatch):
    _setup(monkeypatch, 55, [1000.0] * 10 + [850.0] * 10)
    assert auto.slots_per_day() == 4


def test_a_big_drop_steps_back_to_three(monkeypatch):
    _setup(monkeypatch, 55, [1000.0] * 10 + [600.0] * 10)
    assert auto.slots_per_day() == 3


def test_unreadable_numbers_post_three(monkeypatch):
    monkeypatch.setattr(auto, "day_number", lambda today=None: 40)

    def broken():
        raise ValueError("bad file")

    monkeypatch.setattr(auto, "_pace_numbers", broken)
    assert auto.slots_per_day() == 3
