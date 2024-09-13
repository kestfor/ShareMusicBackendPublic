import enum

from sqlalchemy import Column, String, Integer, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import ENUM as pgEnum

from sqlalchemy.orm import relationship

from backend.sql.engine import Base


class TableUrl(Base):
    __tablename__ = 'Urls'
    __table_args__ = {"schema": "public"}  # как будто бы необязательно

    track_id: Column = Column("track_id", String, primary_key=True)
    url: Column = Column('url', String, nullable=True)

    def __repr__(self):
        return f"{self.track_id}:{self.url}"


class TableUsers(Base):
    __tablename__ = 'Users'
    __table_args__ = {"schema": "public"}  # как будто бы необязательно

    user_id: Column = Column("user_id", BigInteger, primary_key=True)
    username: Column = Column("username", String)
    photo_url: Column = Column("photo_url", String)
    first_name: Column = Column("first_name", String)
    last_name: Column = Column("last_name", String)
    auth_date: Column = Column("auth_date", Integer)
    hash: Column = Column("hash", String)

    def __repr__(self):
        return f"{self.__dict__}"


class TablePlaylists(Base):
    __tablename__ = 'Playlists'
    __table_args__ = {"schema": "public"}  # как будто бы необязательно

    playlist_id: Column = Column("playlist_id", Integer, primary_key=True, autoincrement=True)
    name: Column = Column("name", String)
    art_uri: Column = Column("art_uri", String)
    user_id: Column = Column("user_id", BigInteger, ForeignKey(TableUsers.user_id))

    user = relationship('TableUsers', foreign_keys='TablePlaylists.user_id')

    def __repr__(self):
        return f"{self.__dict__}"


class TableTracksOnPlaylists(Base):
    __tablename__ = 'TracksOnPlaylists'
    __table_args__ = {"schema": "public"}  # как будто бы необязательно

    id: Column = Column(Integer, primary_key=True)
    playlist_id: Column = Column("playlist_id", Integer, ForeignKey(TablePlaylists.playlist_id))
    track_id: Column = Column("track_id", String, ForeignKey(TableUrl.track_id))

    playlist = relationship('TablePlaylists', foreign_keys='TableTracksOnPlaylists.playlist_id')
    track = relationship('TableUrl', foreign_keys='TableTracksOnPlaylists.track_id')

    def __repr__(self):
        return f"{self.__dict__}"


class TableLikedTracks(Base):
    __tablename__ = 'LikedTracks'
    __table_args__ = {"schema": "public"}  # как будто бы необязательно

    id: Column = Column(Integer, primary_key=True)
    user_id: Column = Column("user_id", BigInteger, ForeignKey(TableUsers.user_id))
    track_id: Column = Column("track_id", String, ForeignKey(TableUrl.track_id))

    user = relationship('TableUsers', foreign_keys='TableLikedTracks.user_id')
    track = relationship('TableUrl', foreign_keys='TableLikedTracks.track_id')

    def __repr__(self):
        return f"{self.__dict__}"


class RelationStatusEnum(enum.Enum):
    first_user_follow = 'first_user_follow'
    second_user_follow = 'second_user_follow'
    friends = 'friends'
    no_relation = 'no_relation'


class TableRelations(Base):
    __tablename__ = 'Relations'
    __table_args__ = {"schema": "public"}  # как будто бы необязательно

    first_user_id: Column = Column("first_user_id", BigInteger, ForeignKey(TableUsers.user_id), primary_key=True)
    second_user_id: Column = Column("second_user_id", BigInteger, ForeignKey(TableUsers.user_id), primary_key=True)
    type: Column = Column(
        pgEnum(RelationStatusEnum, name='relation_type', create_type=True),
        nullable=False)

    # type: # Column = Column(Enum(RelationStatusEnum, name='relation_type', create_type=True), nullable=False)

    # first_user = relationship('TableUsers', foreign_keys='TableUsers.user_id')
    # second_user = relationship('TableUsers', foreign_keys='TableUsers.user_id')

    def __repr__(self):
        return f"{self.__dict__}"