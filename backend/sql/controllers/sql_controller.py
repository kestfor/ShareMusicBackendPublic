from sqlalchemy import select
from backend.sql.tables import TableUrl, TableUsers
from backend.sql.engine import SessionLocal


class SQLController:

    async def verify_hash(self, user_id: str, hash: str):
        res = (await self._session.execute(select(TableUsers.hash).where(TableUsers.user_id == int(user_id)))).all()
        if len(res) > 0:
            return res[0][0] == hash if (len(res[0]) > 0) else False
        return False

    async def is_cached(self, id) -> bool:
        result = await self._session.execute(select(TableUrl.url).where((TableUrl.track_id == id)))
        return len(result.all()) > 0

    def __init__(self):
        self._session = SessionLocal()

    async def __aenter__(self):
        await self._session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.__aexit__(exc_type, exc_val, exc_tb)
