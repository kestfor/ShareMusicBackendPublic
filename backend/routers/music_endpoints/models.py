from pydantic import BaseModel


class LikedTrack(BaseModel):
    user_id: int
    track_id: str
    hash: str


class Track(BaseModel):
    artist: str
    title: str
    duration: int
    id: str


class UpdatePlaylistActions:
    create_playlist_action = 'create_playlist'
    delete_playlist_action = 'delete_playlist'
    delete_track_action = 'delete_track'
    add_track_action = 'add_track'
    rename_action = 'rename'
    change_art_action = 'change_art'


class UpdatePlaylistInfo(BaseModel):
    action: str
    user_id: str
    hash: str
    data: dict
