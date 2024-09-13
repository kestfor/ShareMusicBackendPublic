import asyncio
import urllib
import aiohttp
from bs4 import BeautifulSoup
from backend.parsers.music_parser import AbstractParser, DecodeError, HTMLStructureError, TrackMatch


class KrolikParser(AbstractParser):
    @property
    def source(self):
        return 'https://krolik.biz/search/'

    def __init__(self, session: aiohttp.ClientSession):
        super().__init__(session)

    async def best_match(self, artist: str, track: str, duration: int, old_link=None) -> TrackMatch:
        return await super().best_match(artist, track, duration, old_link=old_link)

    async def _get_variants(self, artist: str, track: str, duration: int) -> dict[str: str]:
        main_query = f"{artist} {track}"
        search = self.source
        main_url = search + urllib.parse.quote(main_query)
        res = await self._session.get(main_url)
        results = []
        if res.status == 200:
            text = await res.text()
            soup = BeautifulSoup(text, 'lxml')
            items = soup.find_all("div", class_='mp3')
            for item in items:
                try:
                    url_block = item.find("div", class_='btns')
                    title_block = item.find("div", class_='title')
                    duration_block = item.find("div", class_='duration')
                    if url_block is not None and title_block is not None and duration_block is not None and url_block.find(
                            "div"):
                        url = url_block.find("div")['data-url'].strip()
                        title = title_block.text.strip().split('\n')
                        artist_found, track_found = title[0], title[-1]
                        duration_found = duration_block.text.strip().split(':')
                        duration_found = int(duration_found[0]) * 60 + int(duration_found[-1])
                        results.append({
                            "url": url,
                            "duration": duration_found,
                            "artist": artist_found.lower().strip(),
                            "track": track_found.lower().strip()
                        })
                except:
                    pass
        return results