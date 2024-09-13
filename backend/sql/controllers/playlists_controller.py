from sqlalchemy import delete, update, select

from backend.sql.controllers.sql_controller import SQLController
from backend.sql.tables import TableTracksOnPlaylists, TablePlaylists, TableUrl


class PlaylistsController(SQLController):

    async def get_tracks(self, playlist_id: int) -> list:
        stmt = select(TableTracksOnPlaylists.track_id).where(TableTracksOnPlaylists.playlist_id == playlist_id)
        response = await self._session.execute(stmt)
        return [row[0] for row in response]

    async def delete_playlist(self, playlist_id: int) -> None:
        await self._session.execute(delete(TableTracksOnPlaylists).where(TableTracksOnPlaylists.playlist_id == playlist_id))
        await self._session.execute(delete(TablePlaylists).where(TablePlaylists.playlist_id == playlist_id))
        await self._session.commit()

    async def delete_track(self, playlist_id: int, track_id: str) -> None:
        await self._session.execute(delete(TableTracksOnPlaylists).where(TableTracksOnPlaylists.track_id == track_id,
                                                                   TableTracksOnPlaylists.playlist_id == playlist_id))
        await self._session.commit()

    async def add_track(self, playlist_id: int, track_id: str) -> None:
        if not await self.is_cashed(track_id):
            self._session.add(TableUrl(track_id=track_id))
        self._session.add(TableTracksOnPlaylists(playlist_id=playlist_id, track_id=track_id))
        await self._session.commit()

    async def rename_playlist(self, playlist_id: int, new_name: str) -> None:
        await self._session.execute(
            update(TablePlaylists).where(TablePlaylists.playlist_id == playlist_id).values(
                name=new_name).execution_options(
                synchronize_session="fetch"))
        await self._session.commit()

    async def change_art_uri(self, playlist_id: int, new_art_uri: str) -> None:
        await self._session.execute(
            update(TablePlaylists).where(TablePlaylists.playlist_id == playlist_id).values(
                art_uri=new_art_uri).execution_options(
                synchronize_session="fetch"))
        await self._session.commit()

    async def create_playlist(self, name: str, art_uri: str, user_id: str) -> None:
        user_id = int(user_id)
        self._session.add(TablePlaylists(name=name, art_uri=art_uri, user_id=user_id))
        await self._session.commit()
        res = await self._session.execute(
            select(TablePlaylists.playlist_id).where(TablePlaylists.name == name, TablePlaylists.art_uri == art_uri,
                                                     TablePlaylists.user_id == user_id))
        return res.all()[-1][0]
