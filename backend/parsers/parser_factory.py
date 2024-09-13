import asyncio
import urllib
import aiohttp
from bs4 import BeautifulSoup
from backend.parsers.music_parser import AbstractParser, DecodeError, HTMLStructureError, TrackMatch


class ParserResult:

    def __init__(self, url: str, additional_info: dict[str, str] | None):
        self._url = url
        if (additional_info is not None) and (isinstance(additional_info, dict)):
            self._additional_info = additional_info.copy()

    @property
    def url(self):
        return self._url

    @property
    def additional_info(self):
        return self._additional_info

    def __str__(self):
        return self._url


class ParserFactory:

    # async def _get_variants(self, artist: str, track: str, duration: int) -> dict[str: str]:
    #     tasks = [asyncio.create_task(parser._get_variants(artist, track, duration)) for parser in self._parsers]
    #     for task in tasks:
    #         await task
    #     res = []
    #     for task in tasks:
    #         res += task.result()
    #     return res

    def __init__(self, *args: AbstractParser):
        self._parsers: list[AbstractParser] = list(args)

    # returns ulr from one of parsers
    async def best_match(self, artist: str, track: str, duration: int, old_link=None) -> ParserResult:
        matches: list[TrackMatch | None] = []
        tasks = [asyncio.create_task(parser.best_match(artist, track, duration, old_link=old_link)) for parser in self._parsers]
        for task in tasks:
            await task
        for task in tasks:
            res = task.result()
            if res is not None:
                matches.append(res)
        max_match = 0
        match_ind = 0
        for i in range(len(matches)):
            curr_match = matches[i].match
            if curr_match > max_match:
                match_ind = i
                max_match = curr_match
        return None if max_match < 0.7 else ParserResult(matches[match_ind].url, matches[match_ind].additional_info)