import json

from datetime import date, datetime, timedelta, timezone, UTC
from enum import StrEnum
from functools import lru_cache
from typing import Any, Optional, Union

type Number = Union[int, float]

__all__ = [
    "OpponentType",
    "Broadcasters",
    "Company",
    "Datapoint",
    "ExternalMediaLink",
    "Match",
    "MatchGame",
    "MatchOpponent",
    "Placement",
    "Player",
    "Series",
    "SquadPlayer",
    "StandingsEntry",
    "StandingsTable",
    "Team",
    "Tournament",
    "Transfer",
    "TeamTemplate",
]


@lru_cache
def _parseIsoDate(date_str: str) -> Optional[date]:
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        return None


@lru_cache
def _parseIsoDateTime(datetime_str: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(datetime_str).replace(tzinfo=UTC)
    except ValueError:
        return None


class OpponentType(StrEnum):
    """
    Enum that defines all valid opponent types in LPDB.
    """

    team = "team"
    solo = "solo"
    duo = "duo"
    trio = "trio"
    quad = "quad"
    literal = "literal"


class LpdbBaseData:
    """
    Base class of all LPDB data
    """

    __raw: dict[str, Any]
    """
    Raw data from LPDB in Python dict form
    """

    def __init__(self, raw: dict[str, Any]):
        self.__raw = raw.copy()

    def _rawGet(self, key: str):
        """
        Gets the value from LPDB data.

        :param key: the key

        :return: the value associated with the key, returns `None` if the key does not exist or the value is an empty string
        """
        value = self.__raw.get(key)
        if value == "":
            return None
        return value

    def __repr__(self):
        return repr(self.__raw)


class LpdbBaseResponseData(LpdbBaseData):
    """
    Base class of all LPDB response data
    """

    @property
    def pageid(self) -> int:
        return self._rawGet("pageid")

    @property
    def pagename(self) -> str:
        return self._rawGet("pagename")

    @property
    def namespace(self) -> int:
        return self._rawGet("namespace")

    @property
    def objectname(self) -> str:
        return self._rawGet("objectname")

    @property
    def extradata(self) -> Optional[dict[str, Any]]:
        return self._rawGet("extradata")

    @property
    def wiki(self) -> str:
        return self._rawGet("wiki")


class Broadcasters(LpdbBaseResponseData):

    @property
    def id(self) -> str:
        return self._rawGet("id")

    @property
    def name(self) -> str:
        return self._rawGet("name")

    @property
    def page(self) -> str:
        return self._rawGet("page")

    @property
    def position(self) -> str:
        return self._rawGet("position")

    @property
    def language(self) -> str:
        return self._rawGet("language")

    @property
    def flag(self) -> str:
        return self._rawGet("flag")

    @property
    def weight(self) -> float:
        return self._rawGet("weight")

    @property
    def date(self) -> Optional[date]:
        return _parseIsoDate(self._rawGet("date"))

    @property
    def parent(self) -> str:
        return self._rawGet("parent")


class Company(LpdbBaseResponseData):

    @property
    def name(self) -> str:
        return self._rawGet("name")

    @property
    def image(self) -> str:
        return self._rawGet("image")

    @property
    def imageurl(self) -> str:
        return self._rawGet("imageurl")

    @property
    def imagedark(self) -> str:
        return self._rawGet("imagedark")

    @property
    def imagedarkurl(self) -> str:
        return self._rawGet("imagedarkurl")

    @property
    def locations(self) -> list:
        return self._rawGet("locations")

    @property
    def parentcompany(self) -> str:
        return self._rawGet("parentcompany")

    @property
    def sistercompany(self) -> str:
        return self._rawGet("sistercompany")

    @property
    def industry(self) -> str:
        return self._rawGet("industry")

    @property
    def foundeddate(self) -> Optional[datetime]:
        return _parseIsoDateTime(self._rawGet("foundeddate"))

    @property
    def defunctdate(self) -> Optional[datetime]:
        return _parseIsoDateTime(self._rawGet("defunctdate"))

    @property
    def defunctfate(self) -> str:
        return self._rawGet("defunctfate")

    @property
    def links(self) -> dict[str, Any]:
        return self._rawGet("links")


class Datapoint(LpdbBaseResponseData):

    @property
    def type(self) -> str:
        return self._rawGet("type")

    @property
    def name(self) -> str:
        return self._rawGet("name")

    @property
    def information(self) -> str:
        return self._rawGet("information")

    @property
    def imageurl(self) -> str:
        return self._rawGet("imageurl")

    @property
    def imagedark(self) -> str:
        return self._rawGet("imagedark")

    @property
    def imagedarkurl(self) -> str:
        return self._rawGet("imagedarkurl")

    @property
    def date(self) -> Optional[datetime]:
        return _parseIsoDateTime(self._rawGet("date"))


class ExternalMediaLink(LpdbBaseResponseData):

    @property
    def title(self) -> str:
        return self._rawGet("title")

    @property
    def translatedtitle(self) -> str:
        return self._rawGet("translatedtitle")

    @property
    def link(self) -> str:
        return self._rawGet("link")

    @property
    def date(self) -> Optional[date]:
        return _parseIsoDate(self._rawGet("date"))

    @property
    def authors(self) -> dict[str, str]:
        return self._rawGet("authors")

    @property
    def language(self) -> str:
        return self._rawGet("language")

    @property
    def publisher(self) -> str:
        return self._rawGet("publisher")

    @property
    def type(self) -> str:
        return self._rawGet("type")


class Match(LpdbBaseResponseData):

    @property
    def match2id(self) -> str:
        return self._rawGet("match2id")

    @property
    def match2bracketid(self) -> str:
        return self._rawGet("match2bracketid")

    @property
    def status(self) -> str:
        return self._rawGet("status")

    @property
    def winner(self) -> str:
        return self._rawGet("winner")

    @property
    def walkover(self) -> str:
        return self._rawGet("walkover")

    @property
    def resulttype(self) -> str:
        return self._rawGet("resulttype")

    @property
    def finished(self) -> bool:
        return bool(self._rawGet("finished"))

    @property
    def mode(self) -> str:
        return self._rawGet("mode")

    @property
    def type(self) -> str:
        return self._rawGet("type")

    @property
    def section(self) -> str:
        return self._rawGet("section")

    @property
    def game(self) -> str:
        return self._rawGet("game")

    @property
    def patch(self) -> str:
        return self._rawGet("patch")

    @property
    def links(self) -> dict[str, Any]:
        return self._rawGet("links")

    @property
    def bestof(self) -> Optional[int]:
        return self._rawGet("bestof")

    @property
    def date(self) -> Optional[datetime]:
        parsed = _parseIsoDateTime(self._rawGet("date"))
        if not self.dateexact:
            return parsed
        elif self.timezone != None:
            return parsed.astimezone(tz=self.timezone)
        return parsed

    @property
    def dateexact(self) -> bool:
        return bool(self._rawGet("dateexact"))

    @property
    def timezone(self) -> Optional[timezone]:
        """
        Timezone information stored in this match.
        """
        if not self.dateexact:
            return None
        elif self.extradata == None:
            return None
        offset: str = self.extradata.get("timezoneoffset")
        if offset == None:
            return None
        sliced_offset = offset.split(":")
        offset_delta = timedelta(
            hours=int(sliced_offset[0]), minutes=int(sliced_offset[1])
        )
        return timezone(offset_delta, name=self.extradata.get("timezoneid"))

    @property
    def stream(self) -> dict[str, Any]:
        return self._rawGet("stream")

    @property
    def vod(self) -> str:
        return self._rawGet("vod")

    @property
    def tournament(self) -> str:
        return self._rawGet("tournament")

    @property
    def parent(self) -> str:
        return self._rawGet("parent")

    @property
    def tickername(self) -> str:
        return self._rawGet("tickername")

    @property
    def shortname(self) -> str:
        return self._rawGet("shortname")

    @property
    def series(self) -> str:
        return self._rawGet("series")

    @property
    def icon(self) -> str:
        return self._rawGet("icon")

    @property
    def iconurl(self) -> str:
        return self._rawGet("iconurl")

    @property
    def icondark(self) -> str:
        return self._rawGet("icondark")

    @property
    def icondarkurl(self) -> str:
        return self._rawGet("icondarkurl")

    @property
    def liquipediatier(self) -> str:
        return self._rawGet("liquipediatier")

    @property
    def liquipediatiertype(self) -> str:
        return self._rawGet("liquipediatiertype")

    @property
    def publishertier(self) -> str:
        return self._rawGet("publishertier")

    @property
    def match2bracketdata(self) -> dict:
        return self._rawGet("match2bracketdata")

    @property
    def tickername(self) -> str:
        return self._rawGet("tickername")

    @property
    def match2games(self) -> list["MatchGame"]:
        return [
            MatchGame(self, match2game) for match2game in self._rawGet("match2games")
        ]

    @property
    def match2opponents(self) -> list["MatchOpponent"]:
        return [
            MatchOpponent(match2opponent)
            for match2opponent in self._rawGet("match2opponents")
        ]


class MatchGame(LpdbBaseData):
    _parent: "Match"

    def __init__(self, parent: "Match", raw: dict[str, Any]):
        super().__init__(raw)
        self._parent = parent

    @property
    def map(self) -> str:
        return self._rawGet("map")

    @property
    def subgroup(self) -> str:
        return self._rawGet("subgroup")

    @property
    def match2gameid(self) -> int:
        return self._rawGet("match2gameid")

    @property
    def scores(self) -> list[Number]:
        return self._rawGet("scores")

    @property
    def opponents(self) -> list[dict]:
        return self._rawGet("opponents")

    @property
    def status(self) -> str:
        return self._rawGet("status")

    @property
    def winner(self) -> str:
        return self._rawGet("winner")

    @property
    def walkover(self):
        return self._rawGet("walkover")

    @property
    def resulttype(self) -> str:
        return self._rawGet("resulttype")

    @property
    def date(self) -> datetime:
        parsed = _parseIsoDateTime(self._rawGet("date"))
        if not self.dateexact:
            return parsed
        return parsed.astimezone(self._parent.timezone)

    @property
    def dateexact(self) -> bool:
        return self.extradata.get("dateexact")

    @property
    def mode(self) -> str:
        return self._rawGet("mode")

    @property
    def type(self) -> str:
        return self._rawGet("type")

    @property
    def game(self) -> str:
        return self._rawGet("game")

    @property
    def patch(self) -> str:
        return self._rawGet("patch")

    @property
    def vod(self) -> str:
        return self._rawGet("vod")

    @property
    def length(self) -> str:
        return self._rawGet("length")

    @property
    def extradata(self) -> Optional[dict[str, Any]]:
        return self._rawGet("extradata")


class MatchOpponent(LpdbBaseData):

    @property
    def id(self) -> int:
        return self._rawGet("id")

    @property
    def type(self) -> OpponentType:
        return OpponentType(self._rawGet("type"))

    @property
    def name(self) -> str:
        return self._rawGet("name")

    @property
    def template(self) -> Optional[str]:
        return self._rawGet("template")

    @property
    def icon(self) -> str:
        return self._rawGet("icon")

    @property
    def score(self) -> Number:
        return self._rawGet("score")

    @property
    def status(self) -> str:
        return self._rawGet("status")

    @property
    def placement(self) -> int:
        return self._rawGet("placement")

    @property
    def match2players(self) -> list[dict]:
        return self._rawGet("match2players")

    @property
    def extradata(self) -> dict:
        return self._rawGet("extradata")

    @property
    def teamtemplate(self) -> Optional["TeamTemplate"]:
        if self.template == None:
            return None
        return TeamTemplate(self._rawGet("teamtemplate"))

    @property
    def extradata(self) -> Optional[dict[str, Any]]:
        return self._rawGet("extradata")


class Placement(LpdbBaseResponseData):

    @property
    def tournament(self) -> str:
        return self._rawGet("tournament")

    @property
    def series(self) -> str:
        return self._rawGet("series")

    @property
    def parent(self) -> str:
        return self._rawGet("parent")

    @property
    def imageurl(self) -> str:
        return self._rawGet("imageurl")

    @property
    def imagedarkurl(self) -> str:
        return self._rawGet("imagedarkurl")

    @property
    def startdate(self) -> Optional[datetime]:
        return _parseIsoDateTime(self._rawGet("startdate"))

    @property
    def date(self) -> Optional[datetime]:
        return _parseIsoDateTime(self._rawGet("date"))

    @property
    def prizemoney(self) -> Number:
        return self._rawGet("placement")

    @property
    def weight(self) -> Number:
        return self._rawGet("weight")

    @property
    def mode(self) -> str:
        return self._rawGet("mode")

    @property
    def type(self) -> str:
        return self._rawGet("type")

    @property
    def liquipediatier(self) -> str:
        return self._rawGet("liquipediatier")

    @property
    def liquipediatiertype(self) -> str:
        return self._rawGet("liquipediatiertype")

    @property
    def publishertier(self) -> str:
        return self._rawGet("publishertier")

    @property
    def icon(self) -> str:
        return self._rawGet("icon")

    @property
    def iconurl(self) -> str:
        return self._rawGet("iconurl")

    @property
    def icondark(self) -> str:
        return self._rawGet("icondark")

    @property
    def icondarkurl(self) -> str:
        return self._rawGet("icondarkurl")

    @property
    def game(self) -> str:
        return self._rawGet("game")

    @property
    def lastvsdata(self) -> dict:
        return self._rawGet("lastvsdata")

    @property
    def opponentname(self) -> str:
        return self._rawGet("opponentname")

    @property
    def opponenttemplate(self) -> Optional[str]:
        return self._rawGet("opponenttemplate")

    @property
    def opponenttype(self) -> OpponentType:
        return OpponentType(self._rawGet("opponenttype"))

    @property
    def opponentplayers(self) -> dict:
        return self._rawGet("opponentplayers")

    @property
    def qualifier(self) -> str:
        return self._rawGet("qualifier")

    @property
    def qualifierpage(self) -> str:
        return self._rawGet("qualifierpage")

    @property
    def qualifierurl(self) -> str:
        return self._rawGet("qualifierurl")


class Player(LpdbBaseResponseData):

    @property
    def id(self) -> str:
        return self._rawGet("id")

    @property
    def alternateid(self) -> str:
        return self._rawGet("alternateid")

    @property
    def name(self) -> str:
        return self._rawGet("name")

    @property
    def localizedname(self) -> str:
        return self._rawGet("localizedname")

    @property
    def type(self) -> str:
        return self._rawGet("type")

    @property
    def nationality(self) -> str:
        return self._rawGet("nationality")

    @property
    def nationality2(self) -> str:
        return self._rawGet("nationality2")

    @property
    def nationality3(self) -> str:
        return self._rawGet("nationality3")

    @property
    def region(self) -> str:
        return self._rawGet("region")

    @property
    def birthdate(self) -> Optional[date]:
        return _parseIsoDate(self._rawGet("birthdate"))

    @property
    def deathdate(self) -> Optional[date]:
        return _parseIsoDate(self._rawGet("deathdate"))

    @property
    def teampagename(self) -> str:
        return self._rawGet("teampagename")

    @property
    def teamtemplate(self) -> str:
        return self._rawGet("teamtemplate")

    @property
    def links(self) -> dict:
        return self._rawGet("links")

    @property
    def status(self) -> str:
        return self._rawGet("status")

    @property
    def earnings(self) -> Number:
        return self._rawGet("earnings")

    @property
    def earningsbyyear(self) -> dict[str, Number]:
        return self._rawGet("earningsbyyear")


class Series(LpdbBaseResponseData):

    @property
    def name(self) -> str:
        return self._rawGet("name")

    @property
    def abbreviation(self) -> str:
        return self._rawGet("abbreviation")

    @property
    def image(self) -> str:
        return self._rawGet("image")

    @property
    def imageurl(self) -> str:
        return self._rawGet("imageurl")

    @property
    def imagedark(self) -> str:
        return self._rawGet("imagedark")

    @property
    def imagedarkurl(self) -> str:
        return self._rawGet("imagedarkurl")

    @property
    def icon(self) -> str:
        return self._rawGet("icon")

    @property
    def iconurl(self) -> str:
        return self._rawGet("iconurl")

    @property
    def icondark(self) -> str:
        return self._rawGet("icondark")

    @property
    def icondarkurl(self) -> str:
        return self._rawGet("icondarkurl")

    @property
    def game(self) -> str:
        return self._rawGet("game")

    @property
    def type(self) -> str:
        return self._rawGet("type")

    @property
    def organizers(self) -> dict:
        return self._rawGet("organizers")

    @property
    def locations(self) -> dict:
        return self._rawGet("locations")

    @property
    def prizepool(self) -> Number:
        return self._rawGet("prizepool")

    @property
    def liquipediatier(self) -> str:
        return self._rawGet("liquipediatier")

    @property
    def liquipediatiertype(self) -> str:
        return self._rawGet("liquipediatiertype")

    @property
    def publishertier(self) -> str:
        return self._rawGet("publishertier")

    @property
    def launcheddate(self) -> date:
        return _parseIsoDate(self._rawGet("launcheddate"))

    @property
    def defunctdate(self) -> date:
        return _parseIsoDate(self._rawGet("defunctdate"))

    @property
    def defunctfate(self) -> str:
        return self._rawGet("defunctfate")

    @property
    def links(self) -> dict:
        return self._rawGet("links")


class SquadPlayer(LpdbBaseResponseData):

    @property
    def id(self) -> str:
        return self._rawGet("id")

    @property
    def link(self) -> str:
        return self._rawGet("link")

    @property
    def name(self) -> str:
        return self._rawGet("name")

    @property
    def nationality(self) -> str:
        return self._rawGet("nationality")

    @property
    def position(self) -> str:
        return self._rawGet("position")

    @property
    def role(self) -> str:
        return self._rawGet("role")

    @property
    def type(self) -> str:
        return self._rawGet("type")

    @property
    def newteam(self) -> str:
        return self._rawGet("newteam")

    @property
    def teamtemplate(self) -> str:
        return self._rawGet("teamtemplate")

    @property
    def newteamtemplate(self) -> str:
        return self._rawGet("newteamtemplate")

    @property
    def status(self) -> str:
        return self._rawGet("status")

    @property
    def joindate(self) -> date:
        return _parseIsoDate(self._rawGet("joindate"))

    @property
    def joindateref(self) -> dict:
        return self._rawGet("joindateref")

    @property
    def leavedate(self) -> date:
        return _parseIsoDate(self._rawGet("leavedate"))

    @property
    def leavedateref(self) -> dict:
        return self._rawGet("leavedateref")

    @property
    def inactivedate(self) -> date:
        return _parseIsoDate(self._rawGet("inactivedate"))

    @property
    def inactivedateref(self) -> dict:
        return self._rawGet("inactivedateref")


class StandingsEntry(LpdbBaseResponseData):

    @property
    def parent(self) -> str:
        return self._rawGet("parent")

    @property
    def standingsindex(self) -> int:
        return self._rawGet("standingsindex")

    @property
    def opponenttype(self) -> OpponentType:
        return OpponentType(self._rawGet("opponenttype"))

    @property
    def opponentname(self) -> str:
        return self._rawGet("opponentname")

    @property
    def opponenttemplate(self) -> str:
        return self._rawGet("opponenttemplate")

    @property
    def opponentplayers(self) -> dict:
        return self._rawGet("opponentplayers")

    @property
    def placement(self) -> int:
        return self._rawGet("placement")

    @property
    def definitestatus(self) -> str:
        return self._rawGet("definitestatus")

    @property
    def currentstatus(self) -> str:
        return self._rawGet("currentstatus")

    @property
    def placementchange(self) -> int:
        return self._rawGet("placementchange")

    @property
    def scoreboard(self) -> dict:
        return self._rawGet("scoreboard")

    @property
    def roundindex(self) -> int:
        return self._rawGet("roundindex")

    @property
    def slotindex(self) -> dict:
        return self._rawGet("slotindex")


class StandingsTable(LpdbBaseResponseData):

    @property
    def parent(self) -> str:
        return self._rawGet("parent")

    @property
    def standingsindex(self) -> int:
        return self._rawGet("standingsindex")

    @property
    def title(self) -> str:
        return self._rawGet("title")

    @property
    def tournament(self) -> str:
        return self._rawGet("tournament")

    @property
    def section(self) -> dict:
        return self._rawGet("section")

    @property
    def type(self) -> int:
        return self._rawGet("type")

    @property
    def matches(self) -> list[str]:
        return self._rawGet("matches")

    @property
    def config(self) -> dict:
        return self._rawGet("config")


class Team(LpdbBaseResponseData):

    @property
    def name(self) -> str:
        return self._rawGet("name")

    @property
    def locations(self) -> dict:
        return self._rawGet("locations")

    @property
    def region(self) -> str:
        return self._rawGet("region")

    @property
    def logo(self) -> str:
        return self._rawGet("logo")

    @property
    def logourl(self) -> str:
        return self._rawGet("logourl")

    @property
    def logodark(self) -> str:
        return self._rawGet("logodark")

    @property
    def logodarkurl(self) -> str:
        return self._rawGet("logodarkurl")

    @property
    def textlesslogourl(self) -> str:
        return self._rawGet("textlesslogourl")

    @property
    def textlesslogodarkurl(self) -> str:
        return self._rawGet("textlesslogodarkurl")

    @property
    def status(self) -> str:
        return self._rawGet("status")

    @property
    def createdate(self) -> Optional[date]:
        return _parseIsoDate(self._rawGet("createdate"))

    @property
    def disbanddate(self) -> Optional[date]:
        return _parseIsoDate(self._rawGet("disbanddate"))

    @property
    def earnings(self) -> Number:
        return self._rawGet("earnings")

    @property
    def earningsbyyear(self) -> dict[str, Number]:
        return self._rawGet("earningsbyyear")

    @property
    def template(self) -> str:
        return self._rawGet("template")

    @property
    def links(self) -> dict:
        return self._rawGet("links")


class Tournament(LpdbBaseResponseData):

    @property
    def name(self) -> str:
        return self._rawGet("name")

    @property
    def shortname(self) -> str:
        return self._rawGet("shortname")

    @property
    def tickername(self) -> str:
        return self._rawGet("tickername")

    @property
    def banner(self) -> str:
        return self._rawGet("banner")

    @property
    def bannerurl(self) -> str:
        return self._rawGet("bannerurl")

    @property
    def bannerdark(self) -> str:
        return self._rawGet("bannerdark")

    @property
    def bannerdarkurl(self) -> str:
        return self._rawGet("bannerdarkurl")

    @property
    def icon(self) -> str:
        return self._rawGet("icon")

    @property
    def iconurl(self) -> str:
        return self._rawGet("iconurl")

    @property
    def icondark(self) -> str:
        return self._rawGet("icondark")

    @property
    def icondarkurl(self) -> str:
        return self._rawGet("icondarkurl")

    @property
    def seriespage(self) -> str:
        return self._rawGet("seriespage")

    @property
    def serieslist(self) -> dict:
        return self._rawGet("serieslist")

    @property
    def previous(self) -> str:
        return self._rawGet("previous")

    @property
    def previous2(self) -> str:
        return self._rawGet("previous2")

    @property
    def next(self) -> str:
        return self._rawGet("next")

    @property
    def next2(self) -> str:
        return self._rawGet("next2")

    @property
    def game(self) -> str:
        return self._rawGet("game")

    @property
    def mode(self) -> str:
        return self._rawGet("mode")

    @property
    def patch(self) -> str:
        return self._rawGet("patch")

    @property
    def endpatch(self) -> str:
        return self._rawGet("endpatch")

    @property
    def type(self) -> str:
        return self._rawGet("type")

    @property
    def organizers(self) -> dict:
        return self._rawGet("organizers")

    @property
    def startdate(self) -> date:
        return _parseIsoDate(self._rawGet("startdate"))

    @property
    def enddate(self) -> date:
        return _parseIsoDate(self._rawGet("enddate"))

    @property
    def sortdate(self) -> date:
        return _parseIsoDate(self._rawGet("sortdate"))

    @property
    def locations(self) -> dict:
        return self._rawGet("locations")

    @property
    def prizepool(self) -> Number:
        return self._rawGet("prizepool")

    @property
    def participantsnumber(self) -> int:
        return self._rawGet("participantsnumber")

    @property
    def liquipediatier(self) -> str:
        return self._rawGet("liquipediatier")

    @property
    def liquipediatiertype(self) -> str:
        return self._rawGet("liquipediatiertype")

    @property
    def publishertier(self) -> str:
        return self._rawGet("publishertier")

    @property
    def status(self) -> dict:
        return self._rawGet("status")

    @property
    def maps(self) -> list[str]:
        map_data: Optional[str] = self._rawGet("maps")
        if map_data == None:
            return None
        return map_data.split(";")

    @property
    def format(self) -> str:
        return self._rawGet("format")

    @property
    def sponsors(self) -> dict:
        return json.loads(self._rawGet("sponsors"))


class Transfer(LpdbBaseResponseData):

    @property
    def player(self) -> str:
        return self._rawGet("player")

    @property
    def nationality(self) -> str:
        return self._rawGet("nationality")

    @property
    def fromteam(self) -> str:
        return self._rawGet("fromteam")

    @property
    def toteam(self) -> str:
        return self._rawGet("toteam")

    @property
    def fromteamtemplate(self) -> str:
        return self._rawGet("fromteamtemplate")

    @property
    def toteamtemplate(self) -> str:
        return self._rawGet("toteamtemplate")

    @property
    def role1(self) -> str:
        return self._rawGet("role1")

    @property
    def role2(self) -> str:
        return self._rawGet("role2")

    @property
    def reference(self) -> dict:
        return self._rawGet("reference")

    @property
    def date(self) -> Optional[datetime]:
        return _parseIsoDateTime(self._rawGet("date"))

    @property
    def wholeteam(self) -> bool:
        return bool(self._rawGet("wholeteam"))


class TeamTemplate(LpdbBaseData):

    @property
    def template(self) -> str:
        return self._rawGet("template")

    @property
    def page(self) -> str:
        return self._rawGet("page")

    @property
    def name(self) -> str:
        return self._rawGet("name")

    @property
    def shortname(self) -> str:
        return self._rawGet("shortname")

    @property
    def bracketname(self) -> str:
        return self._rawGet("bracketname")

    @property
    def image(self) -> str:
        return self._rawGet("image")

    @property
    def imageurl(self) -> str:
        return self._rawGet("imageurl")

    @property
    def imagedark(self) -> str:
        return self._rawGet("imagedark")

    @property
    def imagedarkurl(self) -> str:
        return self._rawGet("imagedarkurl")

    @property
    def legacyimage(self) -> str:
        return self._rawGet("legacyimage")

    @property
    def legacyimageurl(self) -> str:
        return self._rawGet("legacyimageurl")

    @property
    def legacyimagedark(self) -> str:
        return self._rawGet("legacyimagedark")

    @property
    def legacyimagedarkurl(self) -> str:
        return self._rawGet("legacyimagedarkurl")
