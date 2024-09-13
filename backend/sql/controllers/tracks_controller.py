from sqlalchemy import select, delete, update
from backend.sql.tables import *
from backend.sql.controllers.sql_controller import SQLController


class TracksController(SQLController):
    async def get_cached_urls(self):
        result = await self._session.execute(select(TableUrl.url))
        return result.all()

    async def get_cached_urls_by_ids(self, ids: list):
        result = await self._session.execute(
            select(TableUrl.track_id, TableUrl.url).where(TableUrl.track_id.in_(ids), TableUrl.url.isnot(None)))
        res = {}
        for row in result.all():
            res[row[0]] = row[1]
        return res

    async def get_cached_url_by_id(self, id):
        result = await self._session.execute(
            select(TableUrl.url).where((TableUrl.track_id == id), (TableUrl.url.isnot(None))))
        return result.all()

    async def add_urls(self, items: dict):
        if len(items) == 0:
            return
        # item_list = []
        # for key, val in items.items():
        #     item_list.append(TableURL(SpotifyID=key, URL=val))
        # session.add_all(item_list)
        # await session.execute()
        for key, val in items.items():
            if len((await self._session.execute(select(TableUrl.url).where(TableUrl.track_id == key))).all()) > 0:
                # print("fetch")
                stmt = (
                    update(TableUrl)
                    .where(TableUrl.track_id == key)
                    .values(url=val)
                    .execution_options(synchronize_session="fetch")
                )
                await self._session.execute(stmt)
            else:
                # print("merge")
                await self._session.merge(TableUrl(track_id=key, url=val))
        return await self._session.commit()

