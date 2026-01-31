import datetime
import json
import os

import pytest

import lpdb_python as lpdb


@pytest.fixture
def rootdir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def match_data(rootdir: str) -> lpdb.Match:
    with open(os.path.join(rootdir, "data/sample_match_data.json")) as input_file:
        input_data = json.load(input_file)
        return lpdb.Match(input_data)


def test_read_match_data(match_data: lpdb.Match):
    assert match_data.match2id == "Wrd25KnOut_R03-M001"
    assert match_data.date == datetime.datetime(2025, 11, 9, 7, 20, tzinfo=datetime.UTC)

    assert match_data.timezone.utcoffset(None) == datetime.timedelta(hours=8)

    assert match_data.liquipediatier == "1"

    assert match_data.liquipediatiertype == None

    assert match_data.finished

    for match2opponent in match_data.match2opponents:
        assert match2opponent.type == lpdb.OpponentType.team
        assert isinstance(match2opponent.match2players, list)

    for match2game in match_data.match2games:
        assert isinstance(match2game.opponents, list)
