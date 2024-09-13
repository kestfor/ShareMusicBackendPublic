import abc
import asyncio
import logging
import re
import urllib.parse
from abc import ABC

import aiohttp
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Sec-Ch-Ua-Platform': "Windows",
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
}


class ParserErrors(Exception):
    def __init__(self, message=""):
        self.message = message


# raise when couldn't get html doc
class RequestError(ParserErrors):
    pass


# raise when errors in bs4 parsing (maybe html doc was changed)
class HTMLStructureError(ParserErrors):
    pass


# raise when couldn't read html doc
class DecodeError(ParserErrors):
    pass


class TrackMatch:

    def __init__(self, track_match: int, artist_match: int, full_name: str, url: str,
                 additional_info: dict[str, str] = None):
        self._track_match = track_match
        self._artist_match = artist_match
        self._full_name = full_name
        self._additional_info = additional_info
        self._url = url

    @property
    def additional_info(self):
        return self._additional_info

    @property
    def url(self):
        return self._url

    @property
    def match(self):
        return (self._track_match + self._artist_match) / 2


class AbstractParser(ABC):
    MIN_MATCH_TRACK_PERCENT = 0.7

    @property
    def source(self):
        return "source"

    @abc.abstractmethod
    async def _get_variants(self, artist: str, track: str, duration: int) -> dict[str: str]:
        """
        protected method that should make requests through _session, parse it and return dict with keys: ["artist", "track", "url", "duration]
        :param artist: main artist of song
        :param track: name of song
        :param duration: in ms
        :return: dict with fields ["artist", "track", "url", "duration"]
        """
        pass

    @abc.abstractmethod
    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    @staticmethod
    def match_percent(pattern: str, value_to_check: list[str]):
        '''
        :param pattern:
        :param value_to_check:
        :return: 1 if all items of value_to_check in pattern else value in range (0, 1)
        '''
        amount = 0
        len_matched = 0
        for item in value_to_check:
            if item in pattern:
                amount += 1
                len_matched += len(item)
        full_len = len(''.join(value_to_check))
        return len_matched / full_len if full_len != 0 else 1

    @abc.abstractmethod
    async def best_match(self, artist: str, track: str, duration: int, old_link: str = None) -> TrackMatch | None:
        """
        public method that should process data from _get_variants and return url with best artist-track-duration match
        :param artist: main artist of song
        :param track: name of song
        :param duration: in seconds
        :return: url for track
        """

        artist_split = re.sub(r'["\'.,\-_=/\\&:;()]', ' ', artist.strip().lower()).split(' ')
        track_split = re.sub(r'["\'.,\-_=/\\&:;()]', ' ', track.strip().lower()).split(' ')
        artist = ' '.join(i for i in artist_split if i != '')
        variants = await self._get_variants(artist, track, duration)
        track = ' '.join(i for i in track_split if i != '')
        artist_split = artist.split()
        track_split = track.split()
        # is_source_artist_english = all(bool(re.search(r'[a-zA-Z]', alpha)) for alpha in artist)
        best_match = None
        for variant in variants:
            if old_link is None or variant['url'] != old_link:
                full_name = variant["track"] + ' ' + variant["artist"]
                artist_match = AbstractParser.match_percent(full_name, artist_split)
                track_match = AbstractParser.match_percent(full_name, track_split)
                duration_match = abs(duration - variant["duration"]) < 5
                # is_variant_russian: bool = all(bool(re.search(r'[а-яА-Я]', alpha)) for alpha in variant["artist"])
                if duration_match and track_match >= AbstractParser.MIN_MATCH_TRACK_PERCENT and best_match is None:
                    best_match = variant
                    best_match["artist_match"] = artist_match
                    best_match["track_match"] = track_match
                    best_match["full_name"] = full_name
                elif best_match is not None and duration_match and (
                        (best_match["artist_match"] < artist_match and best_match["track_match"] <= track_match) or
                        (best_match["artist_match"] <= artist_match and best_match["track_match"] < track_match) or
                        (best_match["artist_match"] <= artist_match and best_match["track_match"] <= track_match
                         and len(best_match['full_name']) > len(full_name))
                ):
                    # logging.log(msg=best_match, level=logging.INFO)
                    # logging.log(msg=variant, level=logging.INFO)
                    best_match = variant
                    best_match["artist_match"] = artist_match
                    best_match["track_match"] = track_match
                    best_match['full_name'] = full_name
                # if duration_match and artist_match == 1.0 and track_match == 1.0:
                #     return best_match['url']
        if best_match is None:
            return None
        additional_info = {"Referer": "https://muzyet.net/"} if best_match[
                                                                    'url'] is not None and "https://muzyet.net/" in \
                                                                best_match['url'] else None
        return TrackMatch(track_match=best_match['track_match'], artist_match=best_match['artist_match'],
                          full_name=best_match['full_name'], url=best_match['url'], additional_info=additional_info)
