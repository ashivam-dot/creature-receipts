from datetime import datetime,timedelta,timezone
import json
import requests
from ytc.atlas import stats


def test_empty_rss_uses_cloud_counts(monkeypatch):
    expected=[{'video_id':'abcdefghijk','views':123}]
    monkeypatch.setattr(stats,'_rss_feed',lambda:[])
    monkeypatch.setattr(stats,'_cloud_feed',lambda:expected)
    assert stats.feed()==expected


def test_failed_rss_uses_cloud_counts(monkeypatch):
    def failed():raise requests.ConnectionError('offline')
    monkeypatch.setattr(stats,'_rss_feed',failed)
    monkeypatch.setattr(stats,'_cloud_feed',lambda:[{'views':123}])
    assert stats.feed()==[{'views':123}]


def test_cloud_observation_time_controls_rate_and_checkpoint(tmp_path,monkeypatch):
    episode=tmp_path/'content'/'atlas'/'atlas001';episode.mkdir(parents=True)
    (episode/'publish.json').write_text(json.dumps({'title':'Test','youtube_url':'https://www.youtube.com/shorts/abcdefghijk'}))
    now=datetime.now(timezone.utc);observed=now-timedelta(hours=1);published=observed-timedelta(hours=24)
    monkeypatch.setattr(stats,'feed',lambda:[{'video_id':'abcdefghijk','title':'Test','published':published.isoformat(),'views':240,'likes':3,'observed_at':observed.isoformat(),'metric_source':'authenticated-data-api'}])
    row=stats.update(episode.parent,tmp_path)[0]
    assert row['hours']==24.0
    assert row['views_per_hour']==10.0
    checkpoint=json.loads((tmp_path/'analytics'/'atlas-checkpoints'/'atlas001-24h.json').read_text())
    assert checkpoint['collected_at']==observed.isoformat()


def test_old_cloud_counts_cannot_create_fresh_checkpoint(tmp_path,monkeypatch):
    episode=tmp_path/'content'/'atlas'/'atlas001';episode.mkdir(parents=True)
    (episode/'publish.json').write_text(json.dumps({'title':'Test','youtube_url':'https://www.youtube.com/shorts/abcdefghijk'}))
    now=datetime.now(timezone.utc);observed=now-timedelta(hours=9);published=observed-timedelta(hours=24)
    monkeypatch.setattr(stats,'feed',lambda:[{'video_id':'abcdefghijk','title':'Test','published':published.isoformat(),'views':240,'likes':3,'observed_at':observed.isoformat()}])
    row=stats.update(episode.parent,tmp_path)[0]
    assert row['metric_stale'] is True
    assert not (tmp_path/'analytics'/'atlas-checkpoints'/'atlas001-24h.json').exists()
