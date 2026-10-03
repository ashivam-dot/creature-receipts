"""History publishing must never substitute another Buffer YouTube channel."""

import pytest

from ytc import publish


def test_youtube_destination_requires_exact_configured_channel(monkeypatch):
    channels = [
        {"id": "other", "service": "youtube", "isDisconnected": False},
        {"id": "wanted", "service": "youtube", "isDisconnected": False},
    ]
    monkeypatch.setattr(publish, "channels", lambda: channels)
    monkeypatch.delenv("BUFFER_YOUTUBE_CHANNEL_ID", raising=False)
    with pytest.raises(RuntimeError, match="BUFFER_YOUTUBE_CHANNEL_ID is required"):
        publish.youtube_channel_id()

    monkeypatch.setenv("BUFFER_YOUTUBE_CHANNEL_ID", "missing")
    with pytest.raises(RuntimeError, match="missing or has the wrong service"):
        publish.youtube_channel_id()

    monkeypatch.setenv("BUFFER_YOUTUBE_CHANNEL_ID", "wanted")
    assert publish.youtube_channel_id() == "wanted"
    channels[1]["service"] = "instagram"
    with pytest.raises(RuntimeError, match="missing or has the wrong service"):
        publish.youtube_channel_id()
