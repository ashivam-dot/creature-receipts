import json
import pytest
from ytc.atlas import quality
from ytc.atlas.data import Dataset


def test_mixed_reporting_years_are_not_labelled_one_year():
    ds = Dataset('metric', '%', 'WB', 'CC BY', '', {'USA': 1, 'IND': 2}, {'USA': 2024, 'IND': 2022})
    assert ds.year_label == 'latest available 2022–2024'
    ds.years['IND'] = 2024
    assert ds.year_label == '2024'


@pytest.mark.parametrize('finding,previously_tolerated', [
    ("'decreased' heard as 'increased' after 'population'", False),
    ("'growing' heard as 'glowing' after 'population'", True),
    ("'australia' heard as 'austria' after 'in'", True)])
def test_fuzzy_asr_tolerance_never_accepts_changed_direction_words_or_country(finding, previously_tolerated):
    from ytc import check
    ds = Dataset('metric', '%', 'WB', 'CC BY', '', {'AUS': 1}, {'AUS': 2024}, names={'AUS': 'Australia'})
    assert check._asr_noise(finding) == previously_tolerated
    assert not quality.minor_speech_difference(finding, ds)


def test_small_article_noise_remains_visible_but_acceptable():
    ds = Dataset('metric', '%', 'WB', 'CC BY', '', {'USA': 1}, {'USA': 2024})
    assert quality.minor_speech_difference("'the' heard as '(nothing)' after 'in'", ds)


def test_country_value_cannot_borrow_a_unit_denominator():
    from ytc.atlas.episode import AtlasEpisode
    ep = AtlasEpisode.model_validate({'id': 'atlas999', 'title': 'test', 'value_format': '{v:.0f} per 100',
        'dataset': {'kind': 'worldbank', 'label': 'Broadband', 'source': 'WB'}, 'beats': [{'text': 'test'}]})
    ds = Dataset('broadband', 'per 100', 'WB', 'CC BY', '', {'FRA': 49}, {'FRA': 2024}, names={'FRA': 'France'})
    assert quality.entity_value_errors('France has 49 subscriptions per 100 people.', ep, ds) == []
    assert quality.entity_value_errors('France has 100 subscriptions per 100 people.', ep, ds)


def test_digits_in_a_measure_name_are_not_the_country_value():
    from ytc.atlas.episode import AtlasEpisode
    ep = AtlasEpisode.model_validate({'id': 'atlas999', 'title': 'test', 'value_format': '{v:.0f}',
        'dataset': {'kind': 'worldbank', 'label': 'PM2.5', 'source': 'WB'}, 'beats': [{'text': 'test'}]})
    ds = Dataset('pm25', 'micrograms per m³', 'WB', 'CC BY', '', {'QAT': 108, 'IND': 54},
                 {'QAT': 2023, 'IND': 2023}, names={'QAT': 'Qatar', 'IND': 'India'})
    assert quality.entity_value_errors("Qatar has the world's highest average PM2.5 air pollution at 108.", ep, ds) == []
    assert quality.entity_value_errors('India has an average PM2.5 level of 2.5.', ep, ds)
    assert quality.entity_value_errors("Qatar has the world's highest average PM2.5 air pollution at 54.", ep, ds)


def test_public_rating_count_is_not_presented_as_verified_likes(monkeypatch):
    from ytc.atlas import stats
    class Response:
        content = b'''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/">
        <entry><yt:videoId>abcdefghijk</yt:videoId><title>Test</title><published>2026-10-08T00:00:00Z</published>
        <media:group><media:community><media:statistics views="63"/><media:starRating count="8" average="4"/></media:community></media:group></entry></feed>'''
        def raise_for_status(self): pass
    monkeypatch.setattr(stats.requests, 'get', lambda *a, **kw: Response())
    row = stats.feed()[0]
    assert row['views'] == 63
    assert row['public_rating_count'] == 8
    assert row['likes'] is None


def test_definition_threshold_is_allowed_but_remains_separate_from_country_values():
    from ytc.atlas import writer
    ds = Dataset('broadband', 'per 100', 'WB', 'CC BY', '', {'USA': 35}, {'USA': 2024},
                 definition='Fixed subscriptions at speeds of 256 kbit/s or higher.')
    _, allowed, owners = writer.facts(ds, {'kind': 'bins'}, '{v:.0f}')
    assert '256' in allowed
    assert '256' not in owners
    assert '999' not in allowed


@pytest.mark.parametrize('values,years', [({}, {}), ({'USA': float('nan')}, {'USA': 2024}), ({'USA': 1}, {})])
def test_invalid_data_cannot_be_saved(tmp_path, values, years):
    ds = Dataset('metric', '%', 'WB', 'CC BY', '', values, years)
    with pytest.raises(ValueError): ds.save(tmp_path / 'data.json')


def receipt(tmp_path):
    for name in ('atlas.yaml', 'data.json'): (tmp_path / name).write_text(name)
    claims = {'review': {'errors': []}, 'evidence': {'source_response_sha256': 'a' * 64},
              'script_sha256': quality.digest(tmp_path / 'atlas.yaml'),
              'data_sha256': quality.digest(tmp_path / 'data.json')}
    quality.save(tmp_path / 'claims.json', claims)
    qa = {'version': 1, 'passed': True, 'media_sha256': 'abc',
          'script_sha256': claims['script_sha256'], 'data_sha256': claims['data_sha256'],
          'claims_sha256': quality.digest(tmp_path / 'claims.json')}
    quality.save(tmp_path / 'qa.json', qa)
    return qa


def test_publisher_rejects_changed_script_and_different_media(tmp_path):
    receipt(tmp_path)
    assert quality.verify(tmp_path, 'abc')['passed']
    with pytest.raises(ValueError): quality.verify(tmp_path, 'different')
    (tmp_path / 'atlas.yaml').write_text('changed country value')
    with pytest.raises(ValueError, match='atlas.yaml'): quality.verify(tmp_path, 'abc')


def test_publisher_rejects_failed_factual_review_even_if_hashes_match(tmp_path):
    qa = receipt(tmp_path)
    claims = json.loads((tmp_path / 'claims.json').read_text())
    claims['review']['errors'] = [{'reason': 'swapped values'}]
    quality.save(tmp_path / 'claims.json', claims)
    qa['claims_sha256'] = quality.digest(tmp_path / 'claims.json')
    quality.save(tmp_path / 'qa.json', qa)
    with pytest.raises(ValueError, match='factual'): quality.verify(tmp_path, 'abc')


def test_publisher_rejects_missing_source_provenance_even_if_artifact_hashes_match(tmp_path):
    qa = receipt(tmp_path)
    claims = json.loads((tmp_path / 'claims.json').read_text())
    claims['evidence']['source_response_sha256'] = ''
    quality.save(tmp_path / 'claims.json', claims)
    qa['claims_sha256'] = quality.digest(tmp_path / 'claims.json')
    quality.save(tmp_path / 'qa.json', qa)
    with pytest.raises(ValueError, match='source-response'): quality.verify(tmp_path, 'abc')


def test_legacy_or_changed_receipts_do_not_count_toward_producer_reserve(tmp_path, monkeypatch):
    from ytc.atlas import pipeline
    folder = tmp_path / 'atlas001'; folder.mkdir()
    marker = {'id': folder.name, 'modal_volume': pipeline.OUTBOX_VOLUME, 'media_sha256': 'abc'}
    quality.save(folder / 'ready.json', marker)
    monkeypatch.setattr(pipeline, 'EPISODES', tmp_path)
    assert pipeline._waiting() == [folder]
    assert pipeline.ready() == []
    receipt(folder)
    marker['qa_sha256'] = quality.digest(folder / 'qa.json')
    quality.save(folder / 'ready.json', marker)
    assert pipeline.ready() == [folder]
    (folder / 'atlas.yaml').write_text('changed')
    assert pipeline.ready() == []


def test_description_has_stable_identity_and_mixed_year_disclosure():
    from ytc.atlas.episode import AtlasEpisode
    from ytc.atlas.publish import description
    ep = AtlasEpisode.model_validate({'id': 'atlas999', 'title': 'test',
        'dataset': {'kind': 'worldbank', 'label': 'Test', 'source': 'WB'}, 'beats': [{'text': 'test'}]})
    ds = Dataset('metric', '%', 'WB', 'CC BY', '', {'USA': 1, 'IND': 2}, {'USA': 2024, 'IND': 2022})
    text = description(ep, ds)
    assert 'Atlas episode: atlas999' in text
    assert 'latest available 2022–2024' in text


def test_explicit_entity_values_cannot_be_swapped_or_use_generic_allowed_100():
    from ytc.atlas.episode import AtlasEpisode
    ep = AtlasEpisode.model_validate({'id': 'atlas999', 'title': 'test', 'value_format': '{v:.0f}',
        'dataset': {'kind': 'worldbank', 'label': 'Metric', 'source': 'WB'}, 'beats': [{'text': 'test'}]})
    ds = Dataset('metric', 'years', 'WB', 'CC BY', '', {'USA': 79, 'CHN': 78, 'JPN': 84},
                 {'USA': 2024, 'CHN': 2024, 'JPN': 2024}, {'USA': 'United States', 'CHN': 'China', 'JPN': 'Japan'})
    assert quality.entity_value_errors('China is at 79 and USA at 78.', ep, ds)
    assert quality.entity_value_errors('Japan has 100 subscriptions per person.', ep, ds)
    assert quality.entity_value_errors('USA has 79 years and China has 78.', ep, ds) == []


def test_public_checkpoint_does_not_invent_missing_retention(tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone
    from ytc.atlas import stats
    episodes = tmp_path / 'content' / 'atlas'
    folder = episodes / 'atlas001'
    folder.mkdir(parents=True)
    (folder / 'publish.json').write_text(json.dumps({'title': 'Test', 'youtube_url': 'https://www.youtube.com/shorts/abcdefghijk'}))
    published = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
    monkeypatch.setattr(stats, 'feed', lambda: [{'video_id': 'abcdefghijk', 'title': 'Test', 'published': published, 'views': 100, 'likes': 3}])
    rows = stats.update(episodes, tmp_path)
    assert rows[0]['checkpoint_24h']['views'] == 100
    assert 'retention' not in rows[0]
    assert 'unavailable' in rows[0]['analytics_status']
    checkpoint = tmp_path / 'analytics' / 'atlas-checkpoints' / 'atlas001-24h.json'
    before = checkpoint.read_text()
    monkeypatch.setattr(stats, 'feed', lambda: [])
    assert stats.update(episodes, tmp_path)[0]['metric_stale'] is True
    assert checkpoint.read_text() == before


def test_topic_selection_does_not_reward_older_lifetime_counts():
    from ytc.atlas import topics
    stats = [{'title': 'Old', 'views': 1000000}, {'title': 'New', 'views': 100}, {'title': 'Other', 'views': 1}]
    assert 'do not infer' in topics._performance(stats)


def test_cached_camera_push_keeps_map_coordinates():
    from PIL import Image
    from ytc.atlas import draw
    import numpy as np
    image = Image.new('RGB', (draw.W * draw.SS, draw.H * draw.SS), (12, 34, 56))
    assert draw.push_layer(image, 1) is image
    pushed = draw.push_layer(image, 1.05)
    assert pushed.size == image.size
    assert tuple(np.asarray(pushed)[100, 100]) == (12, 34, 56)


def test_invalid_manual_scales_cannot_bypass_refill_checks():
    from ytc.atlas.episode import ScaleSpec
    with pytest.raises(ValueError): ScaleSpec(kind='bins', edges=[20, 10])
    with pytest.raises(ValueError): ScaleSpec(kind='threshold', at=float('nan'))


def test_topic_families_are_rotated_without_changing_niche(tmp_path, monkeypatch):
    from ytc.atlas import pipeline
    topics = tmp_path / 'topics.json'
    topics.write_text(json.dumps({'topics': [
        {'id': 't001', 'dataset': {'indicator': 'SP.POP.GROW'}, 'status': 'used:atlas001'},
        {'id': 't002', 'dataset': {'indicator': 'SP.DYN.TFRT.IN'}, 'status': 'open'},
        {'id': 't003', 'dataset': {'indicator': 'IT.NET.USER.ZS'}, 'status': 'open'}]}))
    monkeypatch.setattr(pipeline, 'TOPICS', topics)
    assert pipeline.pick()['id'] == 't003'


def test_iso_codes_that_are_ordinary_words_do_not_become_country_subjects():
    from ytc.atlas.episode import AtlasEpisode
    ep = AtlasEpisode.model_validate({'id': 'atlas999', 'title': 'test', 'value_format': '{v:.0f} per 100',
        'dataset': {'kind': 'worldbank', 'label': 'Metric', 'source': 'WB'}, 'beats': [{'text': 'test'}]})
    ds = Dataset('metric', 'per 100', 'WB', 'CC BY', '', {'PER': 12, 'AND': 52, 'CHN': 47},
                 {'PER': 2024, 'AND': 2024, 'CHN': 2024}, {'PER': 'Peru', 'AND': 'Andorra', 'CHN': 'China'})
    assert quality.entity_value_errors('China has 47 per 100 and the map is yellow.', ep, ds) == []


def test_atlas_overloaded_model_falls_through_after_one_failure(monkeypatch):
    from ytc import llm
    calls = []
    class Response:
        status_code = 503
        content = b'error'
        def json(self): return {'error': {'message': 'overloaded'}}
    monkeypatch.setattr(llm, '_key', lambda: 'test-key')
    monkeypatch.setattr(llm, '_pace', lambda *a: None)
    monkeypatch.setattr(llm.time, 'sleep', lambda *a: None)
    monkeypatch.setattr(llm, '_resting', {})
    monkeypatch.setattr(llm.requests, 'post', lambda *a, **k: calls.append(k) or Response())
    assert llm._ask('test-model', {'generationConfig': {}}, None, 'atlas review') is llm._NO_ANSWER
    assert len(calls) == 1
    assert calls[0]['timeout'] == (20, 90)


def test_percentage_share_has_mathematical_bounds_but_subscriptions_do_not():
    ds = Dataset('metric', '%', 'WB', 'CC BY', '', {'USA': 101}, {'USA': 2024}, indicator='IT.NET.USER.ZS')
    with pytest.raises(ValueError): ds.validate()
    ds.indicator = 'IT.CEL.SETS.P2'
    ds.validate()


def test_episode_ids_are_not_reused_after_failures_or_at_1000(tmp_path, monkeypatch):
    from ytc.atlas import pipeline
    (tmp_path / 'atlas999-failed-20261008').mkdir()
    monkeypatch.setattr(pipeline, 'EPISODES', tmp_path)
    assert pipeline.next_id() == 'atlas1000'
    assert pipeline.EPISODE_ID.fullmatch('atlas1000')
    (tmp_path / 'atlas1000').mkdir()
    assert pipeline.next_id() == 'atlas1001'


def test_enclave_colors_survive_surrounding_country_paint_order(monkeypatch):
    from ytc.atlas import draw, geo
    world = geo.world()
    subset = {'LSO': world['LSO'], 'ZAF': world['ZAF']}
    boxes = [(iso, i, (r[:,0].min(), r[:,1].min(), r[:,0].max(), r[:,1].max()))
             for iso,c in subset.items() for i,r in enumerate(c.rings)]
    monkeypatch.setattr(geo, 'world', lambda: subset)
    monkeypatch.setattr(draw, '_ring_boxes', lambda: boxes)
    monkeypatch.setattr(draw, '_hole_countries', lambda: {'ZAF'})
    camera = draw.country_camera('ZAF')
    image = draw.map_layer(camera, {'LSO': (240,30,30), 'ZAF': (20,20,200)}, set())
    x,y = draw.screen_point(camera, 'LSO')
    pixel = image.getpixel((int(x*draw.SS), int(y*draw.SS)))
    assert pixel[0] > 200 and pixel[2] < 100


def test_hosted_media_must_match_the_accepted_bytes(monkeypatch):
    import hashlib
    from ytc import publish
    class Response:
        headers = {'content-type': 'video/mp4', 'content-length': '3'}
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def raise_for_status(self): pass
        def iter_content(self, *a): yield b'abc'
    monkeypatch.setattr(publish.requests, 'get', lambda *a, **k: Response())
    sha = hashlib.sha256(b'abc').hexdigest()
    assert publish.fetch_video('https://example.com/video', tries=1, expected_sha256=sha)['sha256'] == sha
    with pytest.raises(RuntimeError, match='accepted video'):
        publish.fetch_video('https://example.com/video', tries=1, expected_sha256='wrong')
