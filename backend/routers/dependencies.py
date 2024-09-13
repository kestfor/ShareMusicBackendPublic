from backend.spotify import AsyncSpotify
from backend.sql.include import *


async def get_spotify():
    async with AsyncSpotify() as session:
        yield session


async def get_db_controller() -> SQLController:
    async with SQLController() as controller:
        yield controller


async def get_tracks_controller() -> TracksController:
    async with TracksController() as controller:
        yield controller


async def get_relations_controller() -> RelationsController:
    async with RelationsController() as controller:
        yield controller


async def get_users_controller() -> UsersController:
    async with UsersController() as controller:
        yield controller


async def get_playlists_controller() -> PlaylistsController:
    async with PlaylistsController() as controller:
        yield controller

