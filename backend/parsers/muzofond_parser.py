import asyncio
import urllib
import aiohttp
from bs4 import BeautifulSoup

from backend.parsers.music_parser import AbstractParser, DecodeError, HTMLStructureError, TrackMatch


class MuzofondParser(AbstractParser):

    @property
    def source(self):
        return "https://muzofond.fm/search/"

    def __init__(self, session: aiohttp.ClientSession):
        super().__init__(session)

    async def _get_variants(self, artist: str, track: str, duration: int) -> list[dict]:
        main_query = f"{track} {artist}"
        search = self.source
        main_url = search + urllib.parse.quote(main_query)
        track_query = f"{track}"
        track_url = search + urllib.parse.quote(track_query)
        tasks = [
            asyncio.create_task(self._session.get(track_url)), asyncio.create_task(self._session.get(main_url))]
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
                a = soup.find_all("li", class_='item')
            except Exception:
                raise HTMLStructureError(f"error while parsing one of urls {main_url}, {track_url}")
            for i in a:
                try:
                    url = i.find("li", class_="play")["data-url"]
                    descr = i.find("div", class_="desc descriptionIs")
                    duration_found = ""
                    if "data-duration" in i.attrs:
                        duration_found = int(i["data-duration"])
                    if i.find("div") is not None:
                        artist_found = descr.find("span", class_="artist").text
                        track_name_found = descr.find("span", class_="track").text
                        variants.append(
                            {
                                "url": url,
                                "artist": artist_found.lower(),
                                "track": track_name_found.lower(),
                                "duration": duration_found})
                except AttributeError as error:
                    continue
        return variants

    async def best_match(self, artist: str, track: str, duration: int, old_link=None) -> TrackMatch:
        return await super().best_match(artist, track, duration, old_link=old_link)