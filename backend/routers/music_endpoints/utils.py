import aiohttp
import asyncio

from backend.parsers.music_parser import headers
from backend.parsers.muzofond_parser import MuzofondParser
from backend.parsers.muzyet_parser import MuzyetParser
from backend.parsers.parser_factory import ParserFactory
from backend.parsers.party_parser import PartyParser
from backend.sql.controllers.tracks_controller import TracksController


def create_factory(session):
    last_parser = PartyParser(session)
    sub_parser = MuzyetParser(session)
    main_parser = MuzofondParser(session)
    return ParserFactory(main_parser, sub_parser, last_parser)


async def gather_data(tracks: list['str'], spotify):
    tasks = []
    while len(tracks) > 0:
        ids = tracks[0:min(len(tracks), 50)]
        tracks = tracks[min(len(tracks), 50):]
        tasks.append(asyncio.create_task(spotify.get_tracks(*ids)))
    await asyncio.gather(*tasks)
    res = []
    for task in tasks:
        res += task.result()
    return res


async def get_mp3(track_list: list, controller: TracksController, test=False):
    async with aiohttp.ClientSession(headers=headers) as session:
        factory = create_factory(session)
        tasks = []
        tasks_id = []
        result_dict = {}
        res = await controller.get_cached_urls_by_ids([i['id'] for i in track_list])
        for track in track_list:
            if track['id'] not in res or res[track['id']].startswith('https://krolik') or test:
                tasks.append(
                    asyncio.create_task(factory.best_match(artist=track['artist'], track=track['title'],
                                                           duration=int(track['duration']))))
                tasks_id.append(track['id'])
            else:
                result_dict[track['id']] = {"url": res[track['id']]}
                if MuzyetParser.name() in res[track['id']]:
                    result_dict[track['id']]["headers"] = MuzyetParser.get_headers()
        need_to_cache = {}
        for task in tasks:
            await task
        try:
            for i in range(len(tasks)):
                id = tasks_id[i]
                url = tasks[i].result().url
                if MuzyetParser.name() in url:
                    result_dict[id] = {"url": url, "headers": MuzyetParser.get_headers()}
                else:
                    result_dict[id] = {"url": url, "headers": None}
                if url is not None:
                    need_to_cache[id] = url
        except:
            pass
        await controller.add_urls(need_to_cache)
        return result_dict


async def update_mp3(track_list: list, controller: TracksController):
    async with aiohttp.ClientSession(headers=headers) as session:
        factory = create_factory(session)
        tasks = []
        tasks_id = []
        result_dict = {}
        res = await controller.get_cached_urls_by_ids([i['id'] for i in track_list])
        for track in track_list:
            tasks.append(
                asyncio.create_task(factory.best_match(artist=track['artist'], track=track['title'],
                                                       duration=int(track['duration']),
                                                       old_link=res[track['id']])))
            tasks_id.append(track['id'])
        need_to_cache = {}
        for task in tasks:
            await task
        try:
            for i in range(len(tasks)):
                id = tasks_id[i]
                url = tasks[i].result().url
                if MuzyetParser.name in url:
                    result_dict[id] = {"url": url, "headers": tasks[i].result().headers}
                else:
                    result_dict[id] = {"url": url, "headers": None}
                if url is not None:
                    need_to_cache[id] = url
        except:
            pass
        await controller.add_urls(need_to_cache)
        return result_dict