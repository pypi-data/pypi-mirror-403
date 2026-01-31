from datetime import date
from http import HTTPStatus
from types import TracebackType
from typing import Any, Literal, Optional, override

import aiohttp

from ..session import AbstractLpdbSession, LpdbDataType, LpdbError

__all__ = ["AsyncLpdbSession"]


class AsyncLpdbSession(AbstractLpdbSession):
    """
    Asynchronous implementation of a LPDB session
    """

    __session: aiohttp.ClientSession

    def __init__(self, api_key, base_url=AbstractLpdbSession.BASE_URL):
        super().__init__(api_key, base_url=base_url)
        self.__session = aiohttp.ClientSession(
            self._base_url, headers=self._get_header()
        )

    def __enter__(self) -> None:
        raise TypeError("Use async with instead")

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        pass

    async def __aenter__(self) -> "AsyncLpdbSession":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.__session.close()

    @staticmethod
    async def get_wikis() -> set[str]:
        async with aiohttp.ClientSession("https://liquipedia.net/") as session:
            async with session.get(
                "api.php",
                params={"action": "listwikis"},
                headers={"accept": "application/json", "accept-encoding": "gzip"},
            ) as response:
                wikis = await response.json()
                return set(wikis["allwikis"].keys())

    @staticmethod
    async def __handle_response(
        response: aiohttp.ClientResponse,
    ) -> list[dict[str, Any]]:
        return AbstractLpdbSession._parse_results(
            response.status, await response.json()
        )

    @override
    async def make_request(
        self,
        lpdb_datatype: LpdbDataType,
        wiki: str | list[str],
        limit: int = 20,
        offset: int = 0,
        conditions: Optional[str] = None,
        query: Optional[str | list[str]] = None,
        order: Optional[str | list[tuple[str, Literal["asc", "desc"]]]] = None,
        groupby: Optional[str | list[tuple[str, Literal["asc", "desc"]]]] = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        if not AbstractLpdbSession._validate_datatype_name(lpdb_datatype):
            raise ValueError(f'Invalid LPDB data type: "{lpdb_datatype}"')
        async with self.__session.get(
            lpdb_datatype,
            params=AbstractLpdbSession._parse_params(
                wiki=wiki,
                limit=limit,
                offset=offset,
                conditions=conditions,
                query=query,
                order=order,
                groupby=groupby,
                **kwargs,
            ),
        ) as response:
            return await AsyncLpdbSession.__handle_response(response)

    @override
    async def make_count_request(
        self,
        lpdb_datatype,
        wiki: str,
        conditions: Optional[str] = None,
    ) -> int:
        response = await self.make_request(
            lpdb_datatype, wiki=wiki, conditions=conditions, query="count::objectname"
        )
        return response[0]["count_objectname"]

    @override
    async def get_team_template(
        self, wiki: str, template: str, date: Optional[date] = None
    ) -> Optional[dict[str, Any]]:
        params = {
            "wiki": wiki,
            "template": template,
        }
        if date != None:
            params["date"] = date.isoformat()
        async with self.__session.get("teamtemplate", params=params) as response:
            parsed_response = await AsyncLpdbSession.__handle_response(response)
            if parsed_response[0] == None:
                return None
            return parsed_response[0]

    @override
    async def get_team_template_list(
        self, wiki: str, pagination: int = 1
    ) -> list[dict[str, Any]]:
        async with self.__session.get(
            "teamtemplatelist",
            params={"wiki": wiki, "pagination": pagination},
        ) as response:
            return await AsyncLpdbSession.__handle_response(response)
