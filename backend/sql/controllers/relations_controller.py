import asyncio

from sqlalchemy import select, update, delete

from backend.sql.controllers.sql_controller import SQLController
from backend.sql.tables import TableRelations, RelationStatusEnum, TableUsers


class RelationsController(SQLController):

    class ActionType:
        first_user_follow = 'first_user_follow'
        second_user_follow = 'second_user_follow'
        first_user_unfollow = 'first_user_unfollow'
        second_user_unfollow = 'second_user_unfollow'

    async def get_relation(self, first_user_id: int, second_user_id: int) -> str | None:
        res = (await self._session.execute(select(TableRelations.type).where(
            (TableRelations.first_user_id == first_user_id),
            (TableRelations.second_user_id == second_user_id)))).first()
        if res is None:
            return res
        return res[0].value

    async def update_relation(self, first_user_id: int, second_user_id: int, action: str) -> str:
        relation = await self.get_relation(first_user_id, second_user_id)
        match relation:
            case None:
                return await self._handle_none_users_relation(first_user_id, second_user_id, action)
            case RelationStatusEnum.first_user_follow.value:
                return await self._handle_first_user_follow_relation(first_user_id, second_user_id, action)
            case RelationStatusEnum.second_user_follow.value:
                return await self._handle_second_user_follow_relation(first_user_id, second_user_id, action)
            case RelationStatusEnum.friends.value:
                return await self._handle_friends_users_relation(first_user_id, second_user_id, action)

    async def _handle_none_users_relation(self, first_user_id, second_user_id, action) -> str:
        if action == "first_user_follow":
            obj = TableRelations(first_user_id=first_user_id, second_user_id=second_user_id,
                                 type=RelationStatusEnum.first_user_follow)
            self._session.add(obj)
            await self._session.commit()
            return RelationStatusEnum.first_user_follow.value
        if action == "second_user_follow":
            obj = TableRelations(first_user_id=first_user_id, second_user_id=second_user_id,
                                 type=RelationStatusEnum.second_user_follow)
            self._session.add(obj)
            await self._session.commit()
            return RelationStatusEnum.second_user_follow.value

    async def _handle_friends_users_relation(self, first_user_id, second_user_id, action) -> str:
        if action == "first_user_unfollow":
            stmt = (
                update(TableRelations)
                .where(
                    TableRelations.first_user_id == first_user_id and TableRelations.second_user_id == second_user_id)
                .values(type=RelationStatusEnum.second_user_follow))
            await self._session.execute(stmt)
            await self._session.commit()
            return RelationStatusEnum.no_relation.value
        if action == "second_user_unfollow":
            stmt = (
                update(TableRelations)
                .where(
                    TableRelations.first_user_id == first_user_id and TableRelations.second_user_id == second_user_id)
                .values(type="first_user_follow"))
            await self._session.execute(stmt)
            await self._session.commit()
            return RelationStatusEnum.no_relation.value
        return RelationStatusEnum.friends.value

    async def _handle_first_user_follow_relation(self, first_user_id, second_user_id, action) -> str:
        if action == "second_user_follow":
            stmt = (
                update(TableRelations)
                .where(
                    TableRelations.first_user_id == first_user_id and TableRelations.second_user_id == second_user_id)
                .values(type=RelationStatusEnum.friends))
            await self._session.execute(stmt)
            await self._session.commit()
            return RelationStatusEnum.friends.value
        if action == "first_user_unfollow":
            stmt = (
                delete(TableRelations)
                .where(
                    TableRelations.first_user_id == first_user_id and TableRelations.second_user_id == second_user_id))
            await self._session.execute(stmt)
            await self._session.commit()
            return RelationStatusEnum.no_relation.value

    async def _handle_second_user_follow_relation(self, first_user_id, second_user_id, action) -> str:
        if action == "first_user_follow":
            stmt = (
                update(TableRelations)
                .where(
                    TableRelations.first_user_id == first_user_id and TableRelations.second_user_id == second_user_id)
                .values(type=RelationStatusEnum.friends))
            await self._session.execute(stmt)
            await self._session.commit()
            return RelationStatusEnum.friends.value
        if action == "second_user_unfollow":
            stmt = (
                delete(TableRelations)
                .where(
                    TableRelations.first_user_id == first_user_id and TableRelations.second_user_id == second_user_id))
            await self._session.execute(stmt)
            await self._session.commit()
            return RelationStatusEnum.no_relation.value

    async def search_for_username(self, query):
        stmt = (select(TableUsers.user_id, TableUsers.username, TableUsers.photo_url, TableUsers.first_name, TableUsers.last_name).where(TableUsers.username.ilike(f"%{query}%")))
        return await self._session.execute(stmt)
