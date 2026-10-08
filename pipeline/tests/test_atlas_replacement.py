from datetime import datetime, timedelta
import pytest
from ytc.atlas import publish
from ytc.atlas.data import Dataset
from ytc.atlas.episode import AtlasEpisode


def setup(tmp_path, monkeypatch):
    ep = AtlasEpisode.model_validate({'id': 'atlas002', 'title': 'Checked title',
        'dataset': {'kind': 'worldbank', 'label': 'Metric', 'source': 'WB'}, 'beats': [{'text': 'test'}]})
    ds = Dataset('metric', '%', 'WB', 'CC BY', '', {'USA': 1}, {'USA': 2024})
    video = tmp_path / 'short.mp4'; video.write_bytes(b'checked bytes')
    due = (datetime.now(publish.pub.AUDIENCE_TZ) + timedelta(days=1)).isoformat()
    old = {'id': ep.id, 'buffer_post_id': 'post1', 'title': 'Old title', 'media_url': 'https://old/video.mp4', 'due_at': due}
    current = {'id': 'post1', 'status': 'scheduled', 'title': old['title'], 'video': old['media_url'],
               'dueAt': due, 'text': 'Old description', 'privacy': 'public'}
    new_url = 'https://res.cloudinary.com/cloud/video/upload/v1/atlasinnumbers/atlas002-qa-'
    from ytc.atlas.receipt import digest
    new_url += digest(video)[:12] + '.mp4'
    mutations = []
    monkeypatch.setattr(publish.pub, 'post', lambda _: dict(current))
    monkeypatch.setattr(publish.pub, 'host_video', lambda *a: new_url)
    monkeypatch.setattr(publish.pub, 'fetch_video', lambda url, **kw: {'sha256': kw['expected_sha256']})
    def edit(query, variables):
        payload = variables['input']; mutations.append(payload)
        current.update(title=payload['metadata']['youtube']['title'], text=payload['text'],
                       video=payload['assets'][0]['video']['url'])
        return {'editPost': {'__typename': 'PostActionSuccess'}}
    monkeypatch.setattr(publish.pub, '_buffer', edit)
    return ep, ds, video, old, current, new_url, mutations


def test_checked_replacement_preserves_post_and_slot_and_recovers_retry(tmp_path, monkeypatch):
    ep, ds, video, old, current, new_url, mutations = setup(tmp_path, monkeypatch)
    result = publish.replace_queued(ep, tmp_path, ds, video, old)
    assert result['buffer_post_id'] == old['buffer_post_id']
    assert result['due_at'] == old['due_at']
    assert result['media_url'] == new_url
    assert len(mutations) == 1
    monkeypatch.setattr(publish.pub, 'host_video', lambda *a: pytest.fail('retry must reuse checked hosted bytes'))
    publish.replace_queued(ep, tmp_path, ds, video, old)
    assert len(mutations) == 1


@pytest.mark.parametrize('field,value', [('status', 'sent'), ('title', 'Unexpected edit'), ('video', 'https://other/video.mp4')])
def test_changed_or_sent_post_is_never_edited(tmp_path, monkeypatch, field, value):
    ep, ds, video, old, current, _, mutations = setup(tmp_path, monkeypatch)
    current[field] = value
    with pytest.raises(RuntimeError): publish.replace_queued(ep, tmp_path, ds, video, old)
    assert not mutations
