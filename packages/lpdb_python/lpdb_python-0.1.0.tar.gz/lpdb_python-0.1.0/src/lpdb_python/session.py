from abc import abstractmethod, ABC
from datetime import date
from functools import cache
from http import HTTPStatus
from typing import (
    Any,
    Final,
    Literal,
    NotRequired,
    Optional,
    override,
    Required,
    TypedDict,
    TypeGuard,
)
import re
import warnings

import requests

__all__ = ["LpdbDataType", "LpdbError", "LpdbWarning", "LpdbSession"]

type LpdbDataType = Literal[
    "broadcasters",
    "company",
    "datapoint",
    "externalmedialink",
    "match",
    "placement",
    "player",
    "series",
    "squadplayer",
    "standingsentry",
    "standingstable",
    "team",
    "tournament",
    "transfer",
]


class LpdbResponse(TypedDict):
    """
    Typed representation of a proper LPDB response.
    """

    result: Required[list[dict[str, Any]]]
    """
    The result of the query
    """
    error: NotRequired[list[str]]
    """
    Errors raised by LPDB
    """
    warning: NotRequired[list[str]]
    """
    Non-fatal issues with the LPDB request
    """


class LpdbError(Exception):
    """
    Raised when the LPDB request created a fatal issue.
    """

    pass


class LpdbRateLimitError(LpdbError):
    """
    Raised when the LPDB request created a fatal issue.
    """

    def __init__(self, wiki: str, table: str, *args):
        super().__init__(f'Rate limit reached for table "{table}" in "{wiki}"')
        self.wiki = wiki
        self.table = table


class LpdbWarning(Warning):
    """
    Warnings about LPDB response.
    """

    pass


class AbstractLpdbSession(ABC):
    """
    An abstract LPDB session
    """

    BASE_URL: Final[str] = "https://api.liquipedia.net/api/v3/"

    __DATA_TYPES: Final[frozenset[str]] = frozenset(
        {
            "broadcasters",
            "company",
            "datapoint",
            "externalmedialink",
            "match",
            "placement",
            "player",
            "series",
            "squadplayer",
            "standingsentry",
            "standingstable",
            "team",
            "tournament",
            "transfer",
        }
    )

    __api_key: str

    def __init__(self, api_key: str, base_url: str = BASE_URL):
        self.__api_key = re.sub(r"^ApiKey ", "", api_key)
        self._base_url = base_url

    @cache
    def _get_header(self) -> dict[str, str]:
        return {
            "authorization": f"Apikey {self.__api_key}",
            "accept": "application/json",
            "accept-encoding": "gzip",
        }

    @staticmethod
    def _validate_datatype_name(lpdb_datatype: str) -> TypeGuard[LpdbDataType]:
        return lpdb_datatype in AbstractLpdbSession.__DATA_TYPES

    @staticmethod
    @abstractmethod
    def get_wikis() -> set[str]:
        """
        Fetches the list of all available wikis.

        :return: set of all available wiki names
        """
        pass

    @abstractmethod
    def make_request(
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
        """
        Creates an LPDB query request.

        :param lpdb_datatype: the data type to query
        :param wiki: the wiki(s) to query
        :param limit: the amount of results wanted
        :param offset: the offset, the first `offset` results from the query will be dropped
        :param conditions: the conditions for the query
        :param order: the order of results to be sorted in; each ordering rule is specified as a `(datapoint, direction)` tuple
        :param groupby: the way that the query results are grouped; each grouping rule is specified as a `(datapoint, direction)` tuple

        :returns: result of the query

        :raises ValueError: if an invalid `lpdb_datatype` is supplied
        :raises LpdbError: if something went wrong with the request
        """
        pass

    def make_count_request(
        self,
        lpdb_datatype: LpdbDataType,
        wiki: str,
        conditions: Optional[str] = None,
    ) -> int:
        """
        Queries the number of objects that satisfy the specified condition(s).

        :param lpdb_datatype: the data type to query
        :param wiki: the wiki to query
        :param conditions: the conditions for the query

        :returns: number of objects that satisfy the condition(s)

        :raises ValueError: if an invalid `lpdb_datatype` is supplied
        :raises LpdbError: if something went wrong with the request
        """
        response = self.make_request(
            lpdb_datatype, wiki, conditions=conditions, query="count::objectname"
        )
        return response[0]["count_objectname"]

    @abstractmethod
    def get_team_template(
        self,
        wiki: str,
        template: str,
        date: Optional[date] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Queries a team template from LPDB.

        :param wiki: the wiki to query
        :param template: the name of team template
        :param date: the contextual date for the requested team template

        :returns: the requested team template, may return `None` if the requested team template does not exist

        :raises LpdbError: if something went wrong with the request
        """
        pass

    @abstractmethod
    def get_team_template_list(
        self,
        wiki: str,
        pagination: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Queries a list of team template from LPDB.

        :param wiki: the wiki to query
        :param pagination: used for pagination

        :returns: team templates

        :raises LpdbError: if something went wrong with the request
        """
        pass

    @staticmethod
    def _parse_params(
        wiki: str | list[str],
        limit: int = 20,
        offset: int = 0,
        conditions: Optional[str] = None,
        query: Optional[str | list[str]] = None,
        order: Optional[str | list[tuple[str, Literal["asc", "desc"]]]] = None,
        groupby: Optional[str | list[tuple[str, Literal["asc", "desc"]]]] = None,
        **kwargs,
    ):
        parameters = dict(kwargs)
        if isinstance(wiki, str):
            parameters["wiki"] = wiki
        elif isinstance(wiki, list):
            parameters["wiki"] = ", ".join(wiki)
        else:
            raise TypeError()
        parameters["limit"] = min(limit, 1000)
        parameters["offset"] = offset
        if conditions != None:
            parameters["conditions"] = conditions
        if query != None:
            if isinstance(query, str):
                parameters["query"] = query
            else:
                parameters["query"] = ", ".join(query)
        if order != None:
            if isinstance(order, str):
                parameters["order"] = order
            else:
                parameters["order"] = ", ".join(
                    [f"{order_tuple[0]} {order_tuple[1]}" for order_tuple in order]
                )
        if groupby != None:
            if isinstance(groupby, str):
                parameters["groupby"] = groupby
            else:
                parameters["groupby"] = ", ".join(
                    [
                        f"{groupby_tuple[0]} {groupby_tuple[1]}"
                        for groupby_tuple in groupby
                    ]
                )
        return parameters

    @staticmethod
    def _parse_results(
        status_code: int, response: LpdbResponse
    ) -> list[dict[str, Any]]:
        result = response["result"]
        lpdb_warnings = response.get("warning")
        lpdb_errors = response.get("error")

        if lpdb_errors and len(lpdb_errors) != 0:
            rate_limit = re.match(
                r"API key \"[0-9A-Za-z]+\" limits for wiki \"(?P<wiki>[a-z]+)\" and table \"(?P<table>[a-z]+)\" exceeded\.",
                lpdb_errors[0],
            )
            if rate_limit:
                raise LpdbRateLimitError(
                    wiki=rate_limit.group("wiki"), table=rate_limit.group("table")
                )
            raise LpdbError(re.sub(r"^Error: ?", "", lpdb_errors[0]))
        elif status_code != HTTPStatus.OK:
            status = HTTPStatus(status_code)
            raise LpdbError(f"HTTP {status_code}: {status.name}")
        if lpdb_warnings and len(lpdb_warnings) != 0:
            for lpdb_warning in lpdb_warnings:
                warnings.warn(lpdb_warning, LpdbWarning)
        return result


class LpdbSession(AbstractLpdbSession):
    """
    Implementation of a LPDB session
    """

    @staticmethod
    def get_wikis() -> set[str]:
        response = requests.get(
            "https://liquipedia.net/api.php",
            params={"action": "listwikis"},
            headers={"accept": "application/json", "accept-encoding": "gzip"},
        )
        wikis = response.json()
        return set(wikis["allwikis"].keys())

    @staticmethod
    def __handle_response(response: requests.Response) -> list[dict[str, Any]]:
        status = HTTPStatus(response.status_code)
        return AbstractLpdbSession._parse_results(status, response.json())

    @override
    def make_request(
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
        lpdb_response = requests.get(
            self._base_url + lpdb_datatype,
            headers=self._get_header(),
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
        )
        return LpdbSession.__handle_response(lpdb_response)

    @override
    def get_team_template(
        self, wiki: str, template: str, date: Optional[date] = None
    ) -> Optional[dict[str, Any]]:
        params = {
            "wiki": wiki,
            "template": template,
        }
        if date != None:
            params["date"] = date.isoformat()
        lpdb_response = requests.get(
            self._base_url + "teamtemplate",
            headers=self._get_header(),
            params=params,
        )
        return LpdbSession.__handle_response(lpdb_response)[0]

    @override
    def get_team_template_list(
        self, wiki: str, pagination: int = 1
    ) -> list[dict[str, Any]]:
        lpdb_response = requests.get(
            self._base_url + "teamtemplatelist",
            headers=self._get_header(),
            params={"wiki": wiki, "pagination": pagination},
        )
        return LpdbSession.__handle_response(lpdb_response)
