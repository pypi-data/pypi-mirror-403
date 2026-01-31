import os

import pytest
import pytest_asyncio

import lpdb_python as lpdb
from lpdb_python.async_session import AsyncLpdbSession

KEY = os.getenv("API_KEY")


@pytest_asyncio.fixture
async def async_session() -> AsyncLpdbSession:
    return AsyncLpdbSession(KEY)


@pytest.mark.asyncio
async def test_get_wikis(async_session: AsyncLpdbSession):
    wikis = await async_session.get_wikis()
    assert isinstance(wikis, set)
    # Test with top 5 wikis
    assert {
        "dota2",
        "counterstrike",
        "valorant",
        "mobilelegends",
        "leagueoflegends",
    }.issubset(wikis)


@pytest.mark.asyncio
async def test_make_request_invalid_key():
    with pytest.raises(lpdb.LpdbError):
        async with AsyncLpdbSession("some_random_gibberish") as async_session:
            await async_session.make_request(
                "match",
                "valorant",
                conditions="[[parent::VCT/2025/Stage_1/Masters]]",
                streamurls="true",
            )


@pytest.mark.asyncio
async def test_make_request_invalid_type(async_session: AsyncLpdbSession):
    with pytest.raises(ValueError):
        await async_session.make_request("match2", "valorant")


@pytest.mark.asyncio
async def test_make_request(async_session: AsyncLpdbSession):
    responses = await async_session.make_request(
        "match",
        "valorant",
        conditions="[[parent::VCT/2025/Stage_1/Masters]]",
        streamurls="true",
    )

    for response in responses:
        assert response["parent"] == "VCT/2025/Stage_1/Masters"


@pytest.mark.asyncio
async def test_make_request_with_specific_datapoints(async_session: AsyncLpdbSession):
    responses = await async_session.make_request(
        "match",
        "leagueoflegends",
        conditions="[[parent::VCT/2025/Stage_1/Masters]]",
        query=["parent", "date"],
        streamurls="true",
    )

    for response in responses:
        assert response["parent"] == "VCT/2025/Stage_1/Masters"
        assert isinstance(response["date"], str)
        with pytest.raises(KeyError):
            print(response["liquipediatier"])


@pytest.mark.asyncio
async def test_make_request_with_order(async_session: AsyncLpdbSession):
    responses = await async_session.make_request(
        "match",
        "valorant",
        conditions="[[parent::VCT/2025/Stage_2/Masters]]",
        order=[("date", "asc")],
        streamurls="true",
    )

    for i in range(1, len(responses)):
        assert responses[i - 1]["date"] <= responses[i]["date"]


@pytest.mark.asyncio
async def test_make_count_request(async_session: AsyncLpdbSession):
    responses = await async_session.make_request(
        "match",
        "valorant",
        conditions="[[parent::VCT/2025/Champions]]",
        limit=1000,
    )

    count_response = await async_session.make_count_request(
        "match",
        "valorant",
        conditions="[[parent::VCT/2025/Champions]]",
    )

    assert isinstance(count_response, int)
    assert len(responses) == count_response


@pytest.mark.asyncio
async def test_get_team_template(async_session: AsyncLpdbSession):
    template = await async_session.get_team_template("valorant", "t1")
    assert template["page"] == "T1"


@pytest.mark.asyncio
async def test_get_team_templates(async_session: AsyncLpdbSession):
    templates = await async_session.get_team_template_list("valorant")
    assert isinstance(templates, list)
    for template in templates:
        assert isinstance(template["page"], str)
