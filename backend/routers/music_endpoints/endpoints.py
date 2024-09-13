import json
from typing import Annotated
from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse

from backend.routers.dependencies import *
from backend.routers.music_endpoints.utils import *
from backend.routers.music_endpoints.models import *

router = APIRouter()


@router.get('/playlists/{user_id}', tags=['playlists'])
async def get_user_playlists_endpoint(user_id: int,
                                      controller: Annotated[UsersController, Depends(get_users_controller)]):
    """
    list of dicts {'playlist_id': ..., 'playlist_name': ..., 'artUri': ..., 'tracksId': [...]}
    """
    return Response(content=json.dumps(await controller.get_playlists(user_id)),
                    media_type='application/json;charset=utf-8')


@router.get('playlists/tracks/{playlist_id}/', tags=['playlists'])
async def get_tracks_from_playlist_endpoint(playlist_id: int, controller: Annotated[
    PlaylistsController, Depends(get_playlists_controller)]):
    return Response(content=json.dumps(await controller.get_tracks(playlist_id)),
                    media_type='application/json;charset=utf-8')


@router.post('/playlists/update/', tags=['playlists'])
async def update_user_playlist(update_info: UpdatePlaylistInfo,
                               controller: Annotated[PlaylistsController, Depends(get_playlists_controller)]):
    if not controller.verify_hash(update_info.user_id, update_info.hash):
        return Response(status_code=403)

    match update_info.action:   
        case UpdatePlaylistActions.create_playlist_action:
            res = await controller.create_playlist(update_info.data['name'],
                                                   update_info.data[
                                                       'art_uri'] if 'art_uri' in update_info.data else None,
                                                   update_info.user_id)
            return Response(content=json.dumps({'playlist_id': res}),
                            media_type='application/json;charset=utf-8')
        case UpdatePlaylistActions.delete_playlist_action:
            await controller.delete_playlist(update_info.data['playlist_id'])
        case UpdatePlaylistActions.delete_track_action:
            await controller.delete_track(update_info.data['playlist_id'], update_info.data['track_id'])
        case UpdatePlaylistActions.add_track_action:
            await controller.add_track(update_info.data['playlist_id'], update_info.data['track_id'])
        case UpdatePlaylistActions.rename_action:
            await controller.rename_playlist(update_info.data['playlist_id'], update_info.data['name'])
        case UpdatePlaylistActions.change_art_action:
            await controller.change_art_uri(update_info.data['playlist_id'], update_info.data['art_uri'])
        case _:
            return Response(content='invalid action', status_code=403)


@router.post("/tracks/need_to_update/", tags=["tracks"])
async def update_track_files(tracks: list[Track],
                             controller: Annotated[TracksController, Depends(get_tracks_controller)]):
    return await update_mp3([el.__dict__ for el in tracks], controller)


@router.post("/artists/", tags=["artists"])
async def get_artists(artists: list[str], spotify: AsyncSpotify = Depends(get_spotify)):
    return Response(content=json.dumps(await spotify.get_artists(*artists)),
                    media_type='application/json;charset=utf-8')


@router.get('/liked_tracks/{user_id}', tags=['tracks'])
async def get_liked_tracks(user_id: int, controller: Annotated[UsersController, Depends(get_users_controller)]):
    return await controller.get_liked_tracks(user_id)


@router.post("/tracks/", tags=["tracks"])
async def get_track_file(track: Track, controller: Annotated[TracksController, Depends(get_tracks_controller)]):
    return await get_mp3([track.__dict__], controller)


@router.post("/tracks_from_album/", tags=["tracks"])
async def get_album_tracks(tracks: list[Track],
                           controller: Annotated[TracksController, Depends(get_tracks_controller)]):
    return await get_mp3([el.__dict__ for el in tracks], controller)


@router.get("/search/{q}", tags=["search"])
async def search(q: str, spotify: AsyncSpotify = Depends(get_spotify)):
    data = await spotify.search("track", "album", "artist", request=q)
    content = json.dumps(data, ensure_ascii=False)
    return Response(content=content, media_type='application/json;charset=utf-8')


@router.get("/search/{content_type}/{q}", tags=["search"])
async def search_content(content_type: str, q: str, spotify: AsyncSpotify = Depends(get_spotify)):
    match content_type:
        case "tracks":
            data = await spotify.search_tracks(request=q)
        case "albums":
            data = await spotify.search_albums(request=q)
        case "playlists":
            data = await spotify.search_playlists(request=q)
        case "artists":
            data = await spotify.search_artists(request=q)
        case _:
            return JSONResponse(content={"message": "Invalid content type"}, status_code=404)
    content = json.dumps(data, ensure_ascii=False)
    return Response(content=content, media_type='application/json;charset=utf-8')


@router.get("/full_artist/{id}", tags=["artists"])
async def get_json_full_artist(id: str, spotify: AsyncSpotify = Depends(get_spotify)):
    data = await spotify.get_json_full_artist(id)
    content = json.dumps(data, ensure_ascii=False)
    return Response(content=content, media_type='application/json;charset=utf-8')


@router.get("/albums/{id}", tags=["albums"])
async def get_json_album(id: str, spotify: AsyncSpotify = Depends(get_spotify)):
    data = await spotify.get_json_album(album_id=id)
    content = json.dumps(data, ensure_ascii=False)
    return Response(content=content, media_type='application/json;charset=utf-8')


@router.post("/like/", tags=["user_actions"])
async def like_track(item: LikedTrack, controller: Annotated[UsersController, Depends(get_users_controller)]):
    flag = False
    if await controller.verify_hash(str(item.user_id), item.hash):
        flag = await controller.like_track(str(item.user_id), item.track_id)
    if flag:
        return Response()
    else:
        return Response(status_code=403)


@router.post('/tracks_data/', tags=['tracks'])
async def get_tracks_data(tracks: list['str'], spotify: AsyncSpotify = Depends(get_spotify)):
    data = await gather_data(tracks, spotify)
    content = json.dumps(data, ensure_ascii=False)
    return Response(content=content, media_type='application/json;charset=utf-8')


@router.post("/unlike/", tags=["user_actions"])
async def unlike_track(item: LikedTrack, controller: Annotated[UsersController, Depends(get_users_controller)]):
    item.user_id = int(item.user_id)
    flag = False
    if await controller.verify_hash(str(item.user_id), item.hash):
        flag = await controller.unlike_track(str(item.user_id), item.track_id)
    if flag:
        return Response()
    else:
        return Response(status_code=403)
