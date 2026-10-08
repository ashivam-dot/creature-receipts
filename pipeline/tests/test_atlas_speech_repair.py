import pytest
from ytc.atlas import pipeline
from ytc.atlas.data import Dataset
from ytc.atlas.episode import AtlasEpisode


def setup(tmp_path, monkeypatch, failure):
    monkeypatch.setattr(pipeline, 'EPISODES', tmp_path)
    ds = Dataset('Metric', '%', 'WB', 'CC BY', '', {'USA': 1}, {'USA': 2024},
                 definition='Official definition', source_response_sha256='a' * 64)
    monkeypatch.setattr(pipeline, 'fetch', lambda _: ds)
    monkeypatch.setattr(pipeline.topics, 'audit_dataset', lambda *a: [])
    drafts, reviews, renders = [], [], []
    def write(topic, data, episode_id, **kw):
        drafts.append(topic)
        return AtlasEpisode.model_validate({'id': episode_id, 'title': 'Test',
            'dataset': {'kind': 'worldbank', 'label': 'Metric', 'source': 'WB'},
            'beats': [{'text': f'Checked draft {len(drafts)}'}]})
    monkeypatch.setattr(pipeline.writer, 'write', write)
    monkeypatch.setattr(pipeline.quality, 'review', lambda ep, *a: reviews.append(ep.beats[0].text))
    def render(ep, folder):
        renders.append(ep.beats[0].text)
        video = folder / 'short.mp4'; video.write_bytes(ep.beats[0].text.encode()); return video
    monkeypatch.setattr(pipeline.render, 'render', render)
    def media(ep, *a):
        if len(renders) == 1: raise ValueError(failure)
    monkeypatch.setattr(pipeline.quality, 'media', media)
    return {'id': 't001', 'topic': 'test', 'dataset': {'kind': 'worldbank'}}, drafts, reviews, renders


def test_material_speech_failure_gets_one_rewrite_with_new_factual_and_media_checks(tmp_path, monkeypatch):
    topic, drafts, reviews, renders = setup(tmp_path, monkeypatch, "encoded speech material mismatch: Chad heard as chat")
    ep, folder, _, _ = pipeline.make(topic, 'atlas001')
    assert len(drafts) == len(reviews) == len(renders) == 2
    assert reviews == renders
    assert 'Chad heard as chat' in drafts[1]['angle']
    assert ep.beats[0].text == 'Checked draft 2'
    assert (folder / 'speech-repair.json').exists()


def test_decode_failure_is_not_treated_as_a_script_problem(tmp_path, monkeypatch):
    topic, drafts, reviews, renders = setup(tmp_path, monkeypatch, 'final MP4 failed full decode')
    with pytest.raises(ValueError, match='decode'): pipeline.make(topic, 'atlas001')
    assert len(drafts) == len(reviews) == len(renders) == 1
