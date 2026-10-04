"""A wrong historical image must stop before voice and rendering work."""

import pytest

from ytc import pick


BEATS = [{"text": "On January 12, 1888, the children left their schoolhouse.", "year": 1888}]


def candidate(key, historical):
    return {"key": key, "title": key, "image": b"thumbnail", "historical": historical}


def test_unavailable_or_incomplete_image_check_holds(monkeypatch):
    chosen = {1: candidate("schoolhouse", 1.0)}

    def unavailable(*args, **kwargs):
        raise RuntimeError("model quota exhausted")

    monkeypatch.setattr(pick.llm, "generate", unavailable)
    with pytest.raises(pick.VisualCheckFailed, match="unavailable"):
        pick._verify(BEATS, chosen, "Schoolhouse Blizzard", "image check")

    monkeypatch.setattr(pick.llm, "generate", lambda *args, **kwargs: {"checks": []})
    with pytest.raises(pick.VisualCheckFailed, match="omitted"):
        pick._verify(BEATS, chosen, "Schoolhouse Blizzard", "image check")


def test_image_checker_preserves_resumable_quota_failure(monkeypatch):
    def exhausted(*args, **kwargs):
        raise pick.llm.OutOfQuota("free quota exhausted")

    monkeypatch.setattr(pick.llm, "generate", exhausted)
    with pytest.raises(pick.llm.OutOfQuota):
        pick._verify(BEATS, {1: candidate("schoolhouse", 1.0)}, "Story", "image check")


def test_modern_picture_is_flagged_for_old_event_but_not_present_day_remains():
    modern = {1: candidate("Nebraska State Capitol 2016", 0.0)}
    assert pick._period_problems(BEATS, modern) == {1: "modern-looking image for a historical scene"}
    remains = [{"text": "Today archaeologists inspect the ruins of the 1888 schoolhouse.", "year": 1888}]
    assert pick._period_problems(remains, modern) == {}


def test_replacement_gets_its_own_verification(monkeypatch):
    modern = candidate("Nebraska State Capitol 2016", 0.0)
    period = candidate("Schoolhouse Blizzard 1888 engraving", 1.0)
    checks = []

    def verify(beats, selected, story, purpose):
        checks.append((purpose, list(selected)))
        return {}

    monkeypatch.setattr(pick, "_verify", verify)
    chosen = {1: (modern, [period], {"fit": "close", "box": [0, 0, 1, 1]})}
    used = {modern["key"]}
    result = pick._verified_choices(BEATS, chosen, used, "Schoolhouse Blizzard", "ep060")
    assert result[1][0] is period
    assert result[1][2]["box"] == []
    assert used == {period["key"]}
    assert checks == [("ep060 image check", [1]), ("ep060 replacement image check", [1])]


def test_bad_or_missing_replacement_holds(monkeypatch):
    first = candidate("wrong schoolhouse", 1.0)
    second = candidate("another wrong schoolhouse", 1.0)
    monkeypatch.setattr(pick, "_verify", lambda beats, selected, story, purpose: {1: "wrong event"})
    with pytest.raises(pick.VisualCheckFailed, match="replacement image failed"):
        pick._verified_choices(BEATS, {1: (first, [second], {})}, {first["key"]}, "Story", "ep063")
    with pytest.raises(pick.VisualCheckFailed, match="no verified alternative"):
        pick._verified_choices(BEATS, {1: (first, [], {})}, {first["key"]}, "Story", "ep063")
