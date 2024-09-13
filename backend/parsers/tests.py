import time

import aiohttp
import requests

from muzyet_parser import *
from muzofond_parser import *
from krolik_parser import *
from parser_factory import *
from party_parser import *
from backend.parsers.music_parser import headers


async def test():
    track = requests.get("https://cdn.muzyet.com/?h=JGraYpdVSDEau6Z9dThRNczuddice5G-RL6XLXUfvmc_Wdsvf0o8UvCdY43JSWQ10wtU", headers={"Referer": "https://muzyet.net/"})

    with open("1.mp3", "wb") as f:
        f.write(track.content)
    # artist = "Eminem"
    # title = "Renaissance"
    # duration = 98
    # start = time.time()
    # async with aiohttp.ClientSession(headers=headers) as session:
    #     parser1 = PartyParser(session)
    #     parser2 = MuzyetParser(session)
    #     parser3 = MuzofondParser(session)
    #     factory = ParserFactory(parser3, parser1, parser2)
    #     tasks = []
    #     for i in range(1):
    #         tasks.append(asyncio.create_task(factory.best_match(artist, title, duration)))
    #     for task in tasks:
    #         await task
    #         print(task.result())
    # print(time.time() - start)


if __name__ == '__main__':
    asyncio.run(test())