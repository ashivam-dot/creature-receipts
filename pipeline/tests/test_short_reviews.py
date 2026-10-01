"""Offline checks of the per-Short checkpoints (review.py, auto.review_shorts), with YouTube, the language model,
and the phone faked."""

import json
from datetime import datetime, timedelta, timezone

import pytest
import yaml

from ytc import auto, review, youtube

NOW = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)


def test_due_takes_the_latest_checkpoint_passed_once():
    published = NOW - timedelta(hours=30)
    assert review.due(published, NOW, set()) == 24
    assert review.due(published, NOW, {"24"}) is None
    assert review.due(NOW - timedelta(hours=5), NOW, set()) is None
    assert review.due(NOW - timedelta(days=8), NOW, set()) is None


def test_verdict_separates_reach_from_the_script():
    s = review.summary({"views": 1, "likes": 0, "comments": 0, "sources": {"YT_CHANNEL": 1}}, 24)
    assert review.verdict(s, []).startswith("not shown yet")
    s = review.summary({"views": 300, "likes": 18, "comments": 1}, 24)
    assert review.verdict(s, [100, 120, 150]).startswith("ahead of")
    assert review.verdict(s, [400, 500, 600]).startswith("behind")
    assert review.verdict(s, [100]).startswith("shown: 300 views")


def test_summary_reads_retention_and_feed_share():
    numbers = {"views": 200, "likes": 10, "comments": 2, "sources": {"SHORTS": 150, "YT_CHANNEL": 50},
               "analytics": {"views": 200, "engagedViews": 140, "averageViewPercentage": 82.0},
               "retention": [{"at": 0.05, "watching": 0.7}, {"at": 0.5, "watching": 0.55}, {"at": 1.0, "watching": 0.4}]}
    s = review.summary(numbers, 24)
    assert (s["feed_share"], s["engaged_share"], s["watching_at_5"], s["watching_at_end"]) == (0.75, 0.7, 0.7, 0.4)
    assert s["likes_per_100"] == 5.0


@pytest.fixture
def studio(tmp_path, monkeypatch):
    episodes = tmp_path / "content" / "episodes"
    (tmp_path / "kit").mkdir()
    (tmp_path / "kit" / "channel.json").write_text(json.dumps({"name": "Test Channel"}), encoding="utf-8")
    monkeypatch.setattr(auto, "ROOT", tmp_path)
    monkeypatch.setattr(auto, "EPISODES", episodes)
    monkeypatch.setattr(auto, "_now", lambda: NOW)
    pushed = []
    monkeypatch.setattr(review, "push", lambda topic, title, text: pushed.append((title, text)))
    monkeypatch.setenv("YTC_NTFY_TOPIC", "test-topic")
    return episodes, pushed


def _live(episodes, short_id, video_id, hours_ago):
    folder = episodes / short_id
    folder.mkdir(parents=True)
    sent = (NOW - timedelta(hours=hours_ago)).isoformat()
    (folder / "publish.json").write_text(json.dumps({"id": short_id, "status": "sent", "sent_at": sent,
                                                     "youtube_url": f"https://www.youtube.com/shorts/{video_id}"}), encoding="utf-8")
    (folder / "short.yaml").write_text(yaml.safe_dump({"title": f"Title {short_id}", "beats": [{"text": "Hook line."}]}), encoding="utf-8")
    return folder


def test_review_records_tells_the_owner_and_flags_a_channel_hold(studio, monkeypatch):
    episodes, pushed = studio
    ids = {"ep001": "aaaaaaaaaaa", "ep002": "bbbbbbbbbbb", "ep003": "ccccccccccc"}
    for short_id, video_id in ids.items():
        _live(episodes, short_id, video_id, 25)
    monkeypatch.setattr(youtube, "short_numbers", lambda vids: {
        v: {"published": (NOW - timedelta(hours=25)).isoformat(), "views": 1, "likes": 0, "comments": 0,
            "sources": {"YT_CHANNEL": 1}} for v in vids})
    run = auto.Run("test")
    done = auto.review_shorts(run)
    assert len(done) == 3 and all("at 24 h: not shown yet" in d for d in done)
    perf = json.loads((episodes / "ep001" / "performance.json").read_text())
    assert perf["24"]["numbers"]["views"] == 1 and "diagnosis" not in perf["24"]
    assert len(pushed) == 3 and pushed[0][0] == "Test Channel: ep001 at 24 hours"
    assert any("phone number" in a for a in run.owner_action)
    assert auto.review_shorts(auto.Run("test")) == []


def test_a_seen_short_is_diagnosed_and_feeds_the_learnings(studio, monkeypatch):
    episodes, pushed = studio
    _live(episodes, "ep001", "aaaaaaaaaaa", 30)
    monkeypatch.setattr(youtube, "short_numbers", lambda vids: {
        v: {"published": (NOW - timedelta(hours=30)).isoformat(), "views": 300, "likes": 18, "comments": 1,
            "sources": {"SHORTS": 290, "YT_CHANNEL": 10}} for v in vids})
    monkeypatch.setattr(review, "diagnose", lambda *a: {"worked": ["hook held 70% past 2 s"], "hurt": [],
                                                        "change_next": "Open on the number."})
    monkeypatch.setattr(youtube, "save_stats", lambda out: out / "x.json")
    learned = []
    monkeypatch.setattr(auto, "update_learnings", lambda run, analytics: learned.append(1) or {"log": "added a hypothesis"})
    done = auto.review_shorts(auto.Run("test"))
    assert learned and done[-1] == "learnings: added a hypothesis"
    assert "Next Shorts: Open on the number." in pushed[0][1]
    assert auto._reviews(auto.episodes())[0]["change_next"] == "Open on the number."
