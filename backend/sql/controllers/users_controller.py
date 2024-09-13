from sqlalchemy import select, update, delete

from backend.sql.controllers.sql_controller import SQLController
from backend.sql.tables import TableUsers, TableLikedTracks, TablePlaylists, TableTracksOnPlaylists, TableUrl


class UsersController(SQLController):

    async def get_user_info(self, user_id: int) -> dict | None:
        res = (await self._session.execute(select(TableUsers).where(TableUsers.user_id == user_id))).first()
        if res is not None:
            res = res[0]
            return {
                "user_id": res.user_id,
                "username": res.username,
                "photo_url": res.photo_url,
                "first_name": res.first_name,
                'last_name': res.last_name
            }
        else:
            return None

    async def update_user(self, items: dict):
        items['user_id'] = int(items.pop("id"))
        items['auth_date'] = int(items['auth_date'])
        if len((await self._session.execute(
                select(TableUsers.user_id).where(TableUsers.user_id == items["user_id"]))).all()) == 1:
            id = items.pop("user_id")
            items.pop("auth_date")
            stmt = (update(TableUsers).where(TableUsers.user_id == id).values(**items))
            await self._session.execute(stmt)
        else:
            self._session.add(TableUsers(**items))
        return await self._session.commit()

    async def get_liked_tracks(self, user_id: int) -> list[str]:
        res = []
        try:
            stmt = select(TableLikedTracks.track_id).where(TableLikedTracks.user_id == user_id)
            response = (await self._session.execute(stmt)).all()
            for row in response:
                res.append(row[0])
        except Exception as e:
            print(e)
        return res

    async def get_playlists(self, user_id: int) -> list:
        stmt = select(TablePlaylists.playlist_id, TablePlaylists.name, TablePlaylists.art_uri,
                      TableTracksOnPlaylists.track_id).where(TablePlaylists.user_id == user_id).select_from(
            TablePlaylists).join(TableTracksOnPlaylists,
                                 TablePlaylists.playlist_id == TableTracksOnPlaylists.playlist_id,
                                 isouter=True)

        results = await self._session.execute(stmt)

        res_data = {}
        for playlist_id, playlist_name, art_uri, track_id in results:
            if playlist_id not in res_data:
                res_data[playlist_id] = {'playlist_name': playlist_name, "art_uri": art_uri,
                                         'tracks_id': [track_id] if track_id is not None else []}
            elif track_id is not None:
                res_data[playlist_id]['tracks_id'].append(track_id)
        res = []
        for key in res_data.keys():
            res.append({"playlist_id": key})
            res[-1].update(res_data[key])
        return res

    async def unlike_track(self, user_id: str, track_id: str):
        try:
            stmt = delete(TableLikedTracks).where(TableLikedTracks.track_id == track_id,
                                                  TableLikedTracks.user_id == int(user_id))
            await self._session.execute(stmt)
            await self._session.commit()
        except Exception as e:
            return False
        else:
            return True

    async def like_track(self, user_id: str, track_id: str):
        try:
            if not await self.is_cached(track_id):
                self._session.add(TableUrl(track_id=track_id))
            obj = TableLikedTracks(user_id=int(user_id), track_id=track_id)
            self._session.add(obj)
            await self._session.commit()
        except Exception as e:
            print(e)
            return False
        else:
            return True
