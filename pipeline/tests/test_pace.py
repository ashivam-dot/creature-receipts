from ytc import auto


def _setup(monkeypatch, day, engaged, share=None):
    monkeypatch.setattr(auto, "day_number", lambda today=None: day)
    monkeypatch.setattr(auto, "_pace_numbers", lambda: (engaged, share or [0.6] * len(engaged)))


def test_posts_three_reviewed_shorts_a_day_from_the_start(monkeypatch):
    _setup(monkeypatch, 3, [])
    assert auto.slots_per_day() == 3
    _setup(monkeypatch, -1, [])
    assert auto.slots_per_day() == 3


def test_pace_does_not_wait_on_engagement_numbers(monkeypatch):
    _setup(monkeypatch, 55, [4.0] * 20)
    assert auto.slots_per_day() == 3
    monkeypatch.setattr(auto, "day_number", lambda today=None: 40)

    def broken():
        raise ValueError("bad file")

    monkeypatch.setattr(auto, "_pace_numbers", broken)
    assert auto.slots_per_day() == 3
