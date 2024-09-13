import asyncio
import os
import urllib.request
from threading import Thread
import aiohttp
import librosa
import numpy as np
import yt_dlp
from mutagen.mp3 import MP3

from backend.parsers.music_parser import KrolikParser, ParserFactory, MuzofondParser, MuzyetParser, headers

opener = urllib.request.build_opener()
opener.addheaders = tuple(items for items in headers.items())
urllib.request.install_opener(opener)


async def download_ytvid_as_mp3(query: str, path='.'):
    filename = f"{query}.mp3"
    options = {
        'format': 'bestaudio/best',
        'keepvideo': False,
        'outtmpl': f'{path}{filename}',
        "verbose": False
    }
    extractor = 'ytsearch'
    query_dlp = f'{extractor}:{str(query)} audio'
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([query_dlp])
    print("Download complete... {}".format(filename))
    return f'{path}{filename}'


def get_duration(filename):
    return MP3(filename).info.length


def get_audio_distance(audio1, audio2) -> np.ndarray:
    min_size = min(audio1.size, audio2.size)
    audio1 = audio1[:min_size]
    audio2 = audio2[:min_size]
    spectrogram1: np.ndarray = librosa.feature.melspectrogram(y=audio1)
    spectrogram2: np.ndarray = librosa.feature.melspectrogram(y=audio2)
    distance = (np.square(spectrogram1 - spectrogram2)).mean(axis=0)
    return distance


def compare_with_og(og_filename: str, filenames: [list], path='./'):
    og_file, _ = librosa.load(path + og_filename)
    distances = []
    for i in filenames:
        print(og_filename, i)
        file, _ = librosa.load(path + i)
        distances.append(get_audio_distance(og_file, file).mean())
    el = min(distances)
    index = distances.index(el)
    best = filenames[index]
    print(f"best match with {og_filename} is : {best}")
    return index


def create_factory(session):
    main_parser = KrolikParser(session)
    sub_parser = MuzyetParser(session)
    last_parser = MuzofondParser(session)
    return ParserFactory(last_parser, sub_parser, main_parser)


class NewThread(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super().__init__(self, group, target, name, args, kwargs)

    def run(self):
        if self._target != None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return




def download_item(url, path):
    try:
        urllib.request.urlretrieve(url, path)
        print("urlretrieve COMPLETED", url)
        return True
    except Exception as error:
        print("urlretrieve ERROR", url, error)
        return False


async def download_variants(variants, path='./'):
    try:
        threads = []
        counter = 0
        for el in variants:
            threads.append(
                NewThread(target=download_item, args=(el['url'], f"{path}{counter}.mp3",)))
            counter += 1
        result = []
        for thread in threads:
            thread.start()
        for i in range(len(threads)):
            if threads[i].join():
                result.append(f'{i}.mp3')
        print('result')
        print(result)
        return result
    except Exception as er:
        print(f"download variants error {er}")


async def validate_url(track_og):
    TIME_DELTA = 3
    async with aiohttp.ClientSession(headers=headers) as session:
        factory = create_factory(session)
        variants = await factory._get_variants(artist=track_og['artist'], track=track_og['track'],
                                               duration=track_og['duration'])
    tracks_path = f"./{track_og['track']}/"
    track_og_filename = f"{track_og['artist']} - {track_og['track']}.mp3"
    if track_og['track'] not in os.listdir():
        os.mkdir(track_og['track'])
    good_variants = []
    for i in variants:
        if abs(i['duration'] - track_og['duration']) <= TIME_DELTA:
            good_variants.append(i)
    for i in good_variants:
        print(i)
    tasks = [
        asyncio.create_task(download_ytvid_as_mp3(f"{track_og['artist']} - {track_og['track']}", path=tracks_path)),
        asyncio.create_task(download_variants(good_variants, tracks_path))]
    values = await asyncio.gather(*tasks)
    lst = [i for i in values[1] if i]
    print("cкачал")
    print(lst)
    compare_with_og(track_og_filename, lst, path=tracks_path)
    return good_variants


async def main():
    track = {'artist': 'Дора', 'track': 'Втюрилась', 'duration': 124}
    res = await validate_url(track)
    print(res)


res = asyncio.run(main())
