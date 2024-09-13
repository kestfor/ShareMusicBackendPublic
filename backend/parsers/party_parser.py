import asyncio
import urllib

import aiohttp
from bs4 import BeautifulSoup

from backend.parsers.music_parser import AbstractParser, TrackMatch, DecodeError, HTMLStructureError


class PartyParser(AbstractParser):

    _artist_key = "data-js-artist-name"
    _track_key = "data-js-song-title"
    _url_key = "data-js-url"
    _duration_key = "track__info-item"

    @property
    def source(self):
        return "https://mp3party.net/search"

    def __init__(self, session: aiohttp.ClientSession):
        super().__init__(session)

    async def best_match(self, artist: str, track: str, duration: int, old_link=None) -> TrackMatch:
        return await super().best_match(artist, track, duration, old_link=old_link)

    async def _get_variants(self, artist: str, track: str, duration: int) -> list[dict]:
        main_query = f"{artist} {track}"
        search = self.source
        main_url = f'{search}?q={urllib.parse.quote(main_query)}'
        # track_query = f"{track}"
        # track_url = search + urllib.parse.quote(track_query)
        tasks = [asyncio.create_task(self._session.get(main_url))]
        try:
            for task in tasks:
                await task
            results = [await task.result().text() for task in tasks]
        except Exception as error:
            raise DecodeError(str(error))
        variants = []
        for text in results:
            soup = BeautifulSoup(text, "lxml")
            try:
                a = soup.find_all("div", class_='track song-item')
            except Exception:
                raise HTMLStructureError(f"error while parsing one of urls {main_url}")
            for i in a:
                try:
                    i = i.find_next()
                    artist = i.attrs[self._artist_key]
                    title = i.attrs[self._track_key]
                    url = i.attrs[self._url_key]
                    duration_str = i.find_next("div", class_=self._duration_key).text.strip()
                    minutes, seconds = duration_str.split(":")
                    duration = int(minutes) * 60 + int(seconds)
                    variants.append(
                        {
                            "url": url,
                            "artist": artist.lower(),
                            "track": title.lower(),
                            "duration": duration})
                except AttributeError as error:
                    continue
        return variants