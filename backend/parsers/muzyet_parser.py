import asyncio
import urllib
import aiohttp
from bs4 import BeautifulSoup

from backend.parsers.music_parser import AbstractParser, DecodeError, HTMLStructureError, TrackMatch


class MuzyetParser(AbstractParser):
    @property
    def source(self):
        return "https://muzyet.net/search/"

    @staticmethod
    def name():
        return "muzyet"

    @staticmethod
    def get_headers():
        return {"Referer": "https://muzyet.net/"}

    def __init__(self, session: aiohttp.ClientSession):
        super().__init__(session)

    async def _get_variants(self, artist: str, track: str, duration: int) -> dict[str: str]:
        main_query = f"{artist} {track}"
        search = self.source
        main_url = search + main_query.replace(' ', '-')
        track_url = f'{search}{track}'.replace(' ', '-')
        tasks = [asyncio.create_task(self._session.get(main_url)), asyncio.create_task(self._session.get(track_url))]
        #tasks = [asyncio.create_task(self._session.get(main_url))]
        results = []
        for task in tasks:
            await task
        for res in tasks:
            res = res.result()
            if res.status == 200:
                text = await res.text()
                soup = BeautifulSoup(text, 'lxml')
                items = soup.find("body").find_all("item")
                for item in items:
                    duration_block = item.findNext()
                    duration_found = duration_block.find("span").text.split(':')
                    duration_found = int(duration_found[0]) * 60 + int(duration_found[-1])
                    info_block, url_block = duration_block.find_next_sibling().find_all("div")
                    info_block_text = info_block.text
                    artist_found, track_found = info_block_text[0:info_block_text.find('-')], info_block_text[
                                                                                              info_block_text.find(
                                                                                                  '-') + 1:]
                    url_found = url_block["data-id"]
                    results.append({
                        "url": url_found,
                        "duration": duration_found,
                        "artist": artist_found.lower().strip(),
                        "track": track_found.lower().strip(),
                    })
        return results

    async def best_match(self, artist: str, track: str, duration: int, old_link=None) -> TrackMatch:
        return await super().best_match(artist, track, duration, old_link=old_link)