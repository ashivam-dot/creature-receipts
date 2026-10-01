from datetime import date

from ytc import auto, stories


def test_wikidata_years_read_bc_and_ad():
    claim = {"mainsnak": {"datavalue": {"value": {"time": "+1912-04-15T00:00:00Z"}}}}
    assert stories._year(claim) == 1912
    assert stories._year({"mainsnak": {"datavalue": {"value": {"time": "-0216-08-02T00:00:00Z"}}}}) == -216
    assert stories._year({"mainsnak": {}}) is None


def test_whole_wars_and_eras_are_left_out_but_their_battles_stay():
    assert stories.BROAD.search("World War II") and stories.BROAD.search("Minoan civilization")
    assert not stories.BROAD.search("Battle of the Alamo")
    assert not stories.BROAD.search("Fall of Constantinople")


def test_a_strong_story_outranks_a_widely_read_flat_one():
    data = {"topics": {"Radium Girls": {"score": 10, "readers": 60000}, "Dull event": {"score": 4, "readers": 900000}}}
    assert stories.priority("Radium Girls", data) > stories.priority("Dull event", data)
    assert stories.priority("Unscored", data, readers=60000) < stories.priority("Radium Girls", data)


def test_choose_topics_takes_the_strongest_story_and_never_two_series_in_a_row(monkeypatch):
    topics = [{"topic": t, "series": s, "kind": "backlog", "date": None, "status": ""} for t, s in
              [("Flat A", "Lost Cities"), ("Radium Girls", "The Last Hours"), ("B-25 crash", "The Last Hours"),
               ("Flat B", "Lost Cities")]]
    monkeypatch.setattr(auto, "calendar_topics", lambda today=None: topics)
    monkeypatch.setattr(auto, "demand", lambda backlog: {})
    monkeypatch.setattr(auto, "_now", lambda: auto.datetime(2026, 10, 1, tzinfo=auto.IST))
    monkeypatch.setattr(stories, "topic_scores", lambda: {"topics": {"Radium Girls": {"score": 10, "readers": 60000},
                                                                     "B-25 crash": {"score": 9, "readers": 60000}}})
    chosen = [t["topic"] for t in auto.choose_topics(3, [])]
    assert chosen == ["Radium Girls", "Flat A", "B-25 crash"]


def test_new_stories_go_into_their_series_section():
    lines = ["## Backlog", "", "### Lost Cities", "- Pompeii", "", "### The Last Hours", "- Titanic", ""]
    assert auto.insert_backlog(lines, "Lost Cities", "Herculaneum")
    assert lines[:5] == ["## Backlog", "", "### Lost Cities", "- Pompeii", "- Herculaneum"]
    assert not auto.insert_backlog(lines, "No Such Series", "x")
    assert date.today()
