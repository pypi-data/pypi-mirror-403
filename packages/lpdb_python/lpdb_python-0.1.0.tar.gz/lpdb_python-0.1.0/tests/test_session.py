import os

import pytest

import lpdb_python as lpdb

KEY = os.getenv("API_KEY")


@pytest.fixture
def session() -> lpdb.LpdbSession:
    return lpdb.LpdbSession(KEY)


def test_get_wikis(session: lpdb.LpdbSession):
    wikis = session.get_wikis()
    assert isinstance(wikis, set)
    # Test with top 5 wikis
    assert {
        "dota2",
        "counterstrike",
        "valorant",
        "mobilelegends",
        "leagueoflegends",
    }.issubset(wikis)


def test_make_request_invalid_key():
    session = lpdb.LpdbSession("some_random_gibberish")
    with pytest.raises(lpdb.LpdbError):
        session.make_request(
            "match",
            "leagueoflegends",
            conditions="[[parent::World_Championship/2025]]",
            streamurls="true",
        )


def test_make_request_invalid_type(session: lpdb.LpdbSession):
    with pytest.raises(ValueError):
        session.make_request("match2", "leagueoflegends")


def test_make_request_with_specific_datapoints(session: lpdb.LpdbSession):
    responses = session.make_request(
        "match",
        "leagueoflegends",
        conditions="[[parent::World_Championship/2024]]",
        query=["parent", "date"],
        streamurls="true",
    )

    for response in responses:
        assert response["parent"] == "World_Championship/2024"
        assert isinstance(response["date"], str)
        with pytest.raises(KeyError):
            print(response["liquipediatier"])


def test_make_request_with_order(session: lpdb.LpdbSession):
    responses = session.make_request(
        "match",
        "leagueoflegends",
        conditions="[[parent::Mid-Season_Invitational/2025]]",
        order=[("date", "asc")],
        streamurls="true",
    )

    for i in range(1, len(responses)):
        assert responses[i - 1]["date"] <= responses[i]["date"]


def test_make_count_request(session: lpdb.LpdbSession):
    responses = session.make_request(
        "match",
        "leagueoflegends",
        conditions="[[parent::World_Championship/2025]]",
        limit=1000,
    )

    count_response = session.make_count_request(
        "match",
        "leagueoflegends",
        conditions="[[parent::World_Championship/2025]]",
    )

    assert isinstance(count_response, int)
    assert len(responses) == count_response


def test_get_team_template(session: lpdb.LpdbSession):
    template = session.get_team_template("leagueoflegends", "t1")
    assert template["page"] == "T1"


def test_get_team_templates(session: lpdb.LpdbSession):
    templates = session.get_team_template_list("leagueoflegends")
    assert isinstance(templates, list)
    for template in templates:
        assert isinstance(template["page"], str)
