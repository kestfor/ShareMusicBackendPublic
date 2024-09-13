import asyncio
from asyncio import sleep
from http.client import HTTPException
from json import loads, JSONDecodeError

import asyncspotify
import asyncspotify.http
from asyncspotify import AuthenticationError, BadRequest, Unauthorized, Forbidden, NotFound, NotAllowed
from asyncspotify.client import clamp, get_id
from asyncspotify.utils import subslice

import backend.spotify_errors as spotify_errors
from backend.config_reader import Settings


class AsyncSpotify:
    class ModifiedHTTP(asyncspotify.http.HTTP):

        def __init__(self, client, loop=None):
            super().__init__(client, loop)

        async def request(self, route, data=None, json=None, headers=None, authorize=True):
            if authorize:
                auth_header = self.client.auth.header
                if auth_header is None:
                    raise AuthenticationError('Authorize before attempting an authorized request.')

                if headers:
                    headers.update(auth_header)
                else:
                    headers = auth_header

            kw = dict(method=route.method, url=route.url, headers=headers)
            if kw['headers'] is None:
                kw['headers'] = {}
                kw['headers']['Accept-Language'] = 'ru;q=1, en;q=0.9'

            if route.params:
                kw['params'] = route.params
                kw['headers']['Accept-Language'] = 'ru;q=1, en;q=0.9'

            if data:
                kw['data'] = data
                kw['headers']['Accept-Language'] = 'ru;q=1, en;q=0.9'

            if json:
                kw['json'] = json
                kw['headers']['Accept-Language'] = 'ru;q=1, en;q=0.9'
                kw['headers']['Content-Type'] = 'application/json'

            async with self.lock:
                for attempt in range(self._attempts):

                    async with self.session.request(**kw) as r:
                        status_code = r.status
                        headers = r.headers
                        text = await r.text()
                        asyncspotify.log.debug('[%s] %s', status_code, repr(route))

                        try:
                            data = loads(text)
                        except JSONDecodeError:
                            data = None

                        if 200 <= status_code < 300:
                            return data

                        try:
                            error = data['error']['message']
                        except (TypeError, KeyError):
                            error = None

                        if status_code == 429:
                            retry_after = int(headers.get('Retry-After', 1)) + 1
                            asyncspotify.log.warning('Rate limited. Retrying in %s seconds.', retry_after)
                            await sleep(retry_after)
                            continue

                        elif status_code == 400:
                            raise BadRequest(r, error)

                        elif status_code == 401:
                            raise Unauthorized(r, error)

                        elif status_code == 403:
                            raise Forbidden(r, error)

                        elif status_code == 404:
                            raise NotFound(r, error)

                        elif status_code == 405:
                            raise NotAllowed(r, error)

                        elif status_code >= 500:
                            continue

                        else:
                            raise HTTPException(r, 'Unhandled HTTP status code: %s' % status_code)

            raise HTTPException(r, 'Request failed 5 times.')

    class ModifiedClient(asyncspotify.client.Client):
        def __init__(self, auth):
            self.auth = auth(self)
            self.http: AsyncSpotify.ModifiedHTTP = AsyncSpotify.ModifiedHTTP(self)

        async def get_json_album(self, album_id: str, market=None):
            return await self.http.get_album(album_id, market=market)

        async def get_json_full_artist(self, artist_id: str, limit: int, include_groups: str = "single,album",
                                       country=None, offset=None, market=None):
            artist_task = asyncio.create_task(self.http.get_artists(artist_id))
            albums_task = asyncio.create_task(
                self.http.get_artist_albums(artist_id, include_groups=include_groups, country=country,
                                            limit=clamp(limit, 50), offset=offset))
            market = self._ensure_market(market)
            top_track_task = asyncio.create_task(self.http.get_artist_top_tracks(artist_id, market=market))
            tasks = [albums_task, top_track_task, artist_task]
            await asyncio.gather(*tasks)
            res = {"artist": artist_task.result()['artists'][0] if len(artist_task.result()['artists']) > 0 else None,
                   "top_tracks": top_track_task.result()['tracks'],
                   'albums': albums_task.result()['items']}
            return res

        async def get_artists(self, *artist_ids):
            """
            Get several artists.
            :param artist_ids: List of artist Spotify IDs.
            """
            artists = []
            for chunk in subslice(artist_ids, 50):
                data = await self.http.get_artists(','.join(get_id(obj) for obj in chunk))

                for artist_obj in data['artists']:
                    if artist_obj is not None:
                        artists.append(artist_obj)

            return artists

        async def get_tracks(self, *track_ids):
            tracks = []

            for chunk in subslice(track_ids, 50):
                data = await self.http.get_tracks(','.join(get_id(obj) for obj in chunk))

                for track_obj in data['tracks']:
                    if track_obj is not None:
                        tracks.append(track_obj)
            return tracks

        async def search(self, *types, q, limit=20, market=None, offset=None, include_external=None) -> dict:
            '''
            Searches for tracks, artists, albums and/or playlists.

            :param types: One or more of the strings ``track``, ``album``, ``artist``, ``playlist`` or the class equivalents.
            :param str q: The search query. See Spotifys' query construction guide `here. <https://developer.spotify.com/documentation/web-api/reference/search/search/>`_
            :param int limit: How many results of each type to return.
            :param market: ISO-3166-1_ country code or the string ``from_token``.
            :param offset: Where to start the pagination.
            :param include_external: If this is equal to ``audio``, the specified the response will include any relevant audio content that is hosted externally.

            :return: A dict with a key for each type, whose values are a list of instances.
            '''

            actual_types = []
            for type in types:
                if isinstance(type, (asyncspotify.SimpleTrack, asyncspotify.SimpleAlbum, asyncspotify.SimpleArtist,
                                     asyncspotify.SimplePlaylist)):
                    actual_types.append(type._type)
                elif isinstance(type, str):
                    actual_types.append(type.lower())
                else:
                    raise ValueError('Unknown type: %s' % str(type))

            data = await self.http.search(
                q, ','.join(actual_types),
                market=market,
                limit=clamp(limit, 50),
                offset=offset,
                include_external=include_external
            )

            return data

    _track_prefix = 'spotify%3Atrack%3A'
    _album_prefix = 'spotify:album:'
    _playlist_prefix = 'spotify:playlist:'
    _artist_prefix = 'spotify:artist:'

    def __init__(self, configs: Settings = None):
        if configs is None:
            from backend.config_reader import config
            configs = config

        self._auth = asyncspotify.ClientCredentialsFlow(
            client_id=configs.spotify_client_id.get_secret_value(),
            client_secret=configs.spotify_client_secret.get_secret_value(),
        )

        self._session = AsyncSpotify.ModifiedClient(self._auth)
        self._authorized = False

    async def __aenter__(self):
        await self.authorize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def authorize(self):
        """
        opens async client session
        :return:
        """
        if not self._authorized:
            await self._session.authorize()
            self._authorized = True

    def authorized(self):
        """
        checks if client session authorized
        :return:
        """
        return self._authorized

    async def close(self):
        """
        closes async client session
        :return:
        """
        if self._authorized:
            await self._session.close()
            self._authorized = False

    async def get_track(self, track_id: str) -> asyncspotify.FullTrack:
        """
        :param track_id: spotify id of track
        :return: FullTrack object with track info if track id is valid else RequestError
        """
        try:
            return await self._session.get_track(track_id)
        except asyncspotify.exceptions.NotFound:
            raise spotify_errors.RequestError("bad track id")

    async def get_tracks(self, *track_ids):
        try:
            return await self._session.get_tracks(*track_ids)
        except asyncspotify.exceptions.NotFound:
            raise spotify_errors.RequestError("bad tracks id")

    async def get_json_album(self, album_id: str):
        try:
            return await self._session.get_json_album(album_id)
        except asyncspotify.exceptions.NotFound:
            raise spotify_errors.RequestError("bad album id")

    async def get_json_full_artist(self, artist_id: str, limit_albums=50):
        return await self._session.get_json_full_artist(artist_id, limit=limit_albums)

    async def get_album(self, album_id: str) -> asyncspotify.FullAlbum:
        """
        :param album_id: spotify id of album
        :return: FullAlbum object with album info if track id is valid else RequestError
        """
        try:
            return await self._session.get_album(album_id)
        except asyncspotify.exceptions.NotFound:
            raise spotify_errors.RequestError("bad album id")

    @staticmethod
    def get_full_uri(uri: str) -> str:
        """
        :param uri:
        :return: full spotify uri
        """
        if AsyncSpotify._track_prefix not in uri:
            return AsyncSpotify._track_prefix + uri

    async def search(self, *types, request: str, limit: int = 20):
        '''
        :param types: ["track", "album", "playlist", "artist"]
        :param request: human-like request
        :param limit: max amount of response
        :return: dict with key from types
        '''
        try:
            return await self._session.search(*types, q=request, limit=limit)
        except:
            raise spotify_errors.ConnectionError

    async def search_artists(self, request: str, limit: int = 20) -> dict:
        try:
            return await self._session.search("artist", q=request, limit=limit)
        except:
            raise spotify_errors.ConnectionError

    async def get_artists(self, *artist_ids):
        try:
            return await self._session.get_artists(*artist_ids)
        except:
            raise spotify_errors.ConnectionError

    async def search_playlists(self, request: str, limit: int = 20) -> dict:
        try:
            return await self._session.search("playlist", q=request, limit=limit)
        except:
            raise spotify_errors.ConnectionError

    async def search_albums(self, request: str, limit: int = 20) -> dict:
        try:
            return await self._session.search("album", q=request, limit=limit)
        except:
            raise spotify_errors.ConnectionError

    async def search_tracks(self, request: str, limit: int = 20) -> dict:
        try:
            return await self._session.search("track", q=request, limit=limit)
        except:
            raise spotify_errors.ConnectionError
