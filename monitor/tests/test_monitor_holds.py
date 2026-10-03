"""The watchdog must distinguish deliberate privacy and scheduling holds from failures."""

import datetime as dt

from monitor.monitor import assess


def test_private_sent_posts_and_editorial_pause_do_not_raise_false_delivery_alerts():
    now = dt.datetime.now(dt.timezone.utc)
    sent = (now - dt.timedelta(hours=4)).isoformat()
    data = {
        "github": {
            "status": {"inventory": {"total": 6}},
            "runs": [],
            "history": [{"result": "ok", "started_at_utc": now.isoformat(), "seconds": 1}],
            "workflow_state": "active",
            "minutes": 0,
            "scheduling_hold": {"reason": "Source review pending"},
            "private_videos": {"videos": [{"episode_id": "ep025", "youtube_video_id": "qtmFWWw0npA",
                                           "privacy_status": "private"}]},
        },
        "buffer": {
            "scheduled": [],
            "sent": [
                {"sentAt": sent, "externalLink": "https://www.youtube.com/shorts/qtmFWWw0npA",
                 "metadata": {"title": "Intentionally private"}},
                {"sentAt": sent, "externalLink": "https://www.youtube.com/shorts/ABCDEFGHIJK",
                 "metadata": {"title": "Unexpected absence"}},
            ],
            "channel": {"isDisconnected": False, "isLocked": False, "isQueuePaused": False},
        },
        "feed": [{"id": "v4rp0oWvgSI", "title": "Winton", "published": now.isoformat()}],
    }

    problems = assess(data)
    messages = [message for _, message in problems]
    assert any("Source review pending" in message for message in messages)
    assert any("Unexpected absence" in message for message in messages)
    assert not any("Intentionally private" in message for message in messages)
    assert not any("Buffer has nothing scheduled" in message for message in messages)


def test_empty_queue_without_hold_remains_an_alert():
    now = dt.datetime.now(dt.timezone.utc)
    data = {
        "github": {
            "status": {"inventory": {"total": 6}},
            "runs": [],
            "history": [{"result": "ok", "started_at_utc": now.isoformat(), "seconds": 1}],
            "workflow_state": "active",
            "minutes": 0,
        },
        "buffer": {"scheduled": [], "sent": [], "channel": {}},
    }
    problems = assess(data)
    assert ("alert", "Buffer has nothing scheduled: no Shorts will go out.") in problems


def test_strict_editorial_hold_alerts_if_buffer_queue_is_not_empty():
    now = dt.datetime.now(dt.timezone.utc)
    data = {
        "github": {
            "status": {"inventory": {"total": 0}},
            "runs": [],
            "history": [{"result": "ok", "started_at_utc": now.isoformat(), "seconds": 1}],
            "workflow_state": "active",
            "minutes": 0,
            "scheduling_hold": {"reason": "Review pending", "block_existing_queue": True},
        },
        "buffer": {
            "scheduled": [{"id": "p1", "dueAt": (now + dt.timedelta(hours=2)).isoformat()}],
            "sent": [],
            "channel": {"isDisconnected": False, "isLocked": False, "isQueuePaused": False},
        },
    }

    problems = assess(data)
    assert ("alert", "Editorial hold requires an empty Buffer queue, but 1 post(s) are scheduled. "
            "Pause the YouTube queue in Buffer now, then remove the posts; "
            "the hold does not stop posts already queued in Buffer.") in problems


def test_strict_hold_exempts_only_explicit_approved_buffer_post():
    now = dt.datetime.now(dt.timezone.utc)
    data = {
        "github": {
            "status": {"inventory": {"total": 0}}, "runs": [],
            "history": [{"result": "ok", "started_at_utc": now.isoformat(), "seconds": 1}],
            "workflow_state": "active", "minutes": 0,
            "scheduling_hold": {"reason": "Review pending", "block_existing_queue": True,
                                "approved_buffer_post_id": "approved-post"},
        },
        "buffer": {
            "scheduled": [{"id": "approved-post", "dueAt": (now + dt.timedelta(hours=2)).isoformat()}],
            "sent": [], "channel": {"isDisconnected": False, "isLocked": False, "isQueuePaused": False},
        },
    }
    assert not any("Editorial hold requires an empty Buffer queue" in message for _, message in assess(data))

    data["buffer"]["scheduled"].append({"id": "unexpected-post", "dueAt": (now + dt.timedelta(hours=3)).isoformat()})
    assert ("alert", "Editorial hold permits only Buffer post approved-post, but 1 other post(s) are scheduled. "
            "Pause the YouTube queue in Buffer now, then remove the posts; "
            "the hold does not stop posts already queued in Buffer.") in assess(data)


def test_approved_sent_post_alerts_when_public_feed_is_still_empty():
    now = dt.datetime.now(dt.timezone.utc)
    data = {
        "github": {
            "status": {"inventory": {"total": 0}}, "runs": [],
            "history": [{"result": "ok", "started_at_utc": now.isoformat(), "seconds": 1}],
            "workflow_state": "active", "minutes": 0,
            "scheduling_hold": {"reason": "Other releases paused", "block_existing_queue": True,
                                "approved_buffer_post_id": "approved-post"},
        },
        "buffer": {
            "scheduled": [], "errors": [],
            "sent": [{"id": "approved-post", "sentAt": (now - dt.timedelta(minutes=100)).isoformat(),
                      "externalLink": "https://www.youtube.com/shorts/ABCDEFGHIJK",
                      "metadata": {"title": "Reviewed first release"}}],
            "channel": {"isDisconnected": False, "isLocked": False, "isQueuePaused": False},
        },
        "feed": [],
    }
    assert any(level == "alert" and "Reviewed first release" in message
               for level, message in assess(data))


def test_approved_post_still_queued_after_slot_alerts_only_with_fresh_buffer_read():
    now = dt.datetime.now(dt.timezone.utc)
    due = now - dt.timedelta(hours=1)
    data = {
        "github": {
            "status": {"inventory": {"total": 0}}, "runs": [],
            "history": [{"result": "ok", "started_at_utc": now.isoformat(), "seconds": 1}],
            "workflow_state": "active", "minutes": 0,
            "scheduling_hold": {"reason": "Other releases paused", "block_existing_queue": True,
                                "approved_buffer_post_id": "approved-post"},
        },
        "buffer": {
            "checked_at": (due + dt.timedelta(minutes=20)).isoformat(),
            "scheduled": [{"id": "approved-post", "dueAt": due.isoformat()}],
            "sent": [], "errors": [],
            "channel": {"isDisconnected": False, "isLocked": False, "isQueuePaused": False},
        },
    }
    assert not any("approved-post is still awaiting send" in message for _, message in assess(data))

    data["buffer"]["checked_at"] = now.isoformat()
    assert any(level == "alert" and "approved-post is still awaiting send" in message
               for level, message in assess(data))
