from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# Domain classes for modelling Discord interactions


@dataclass(frozen=True)
class Target:
    """
    Base class for a Discord entity associated with a Model.
    E.g. if a Model models speech patterns of a user, this user is the target.
    """

    @property
    def server_id(self) -> int:
        return self.server.id if hasattr(self, 'server') else 0

    @property
    def key(self) -> any:
        if hasattr(self, 'id'):
            return self.id
        return self


@dataclass(frozen=True)
class Server(Target):
    id: int
    name: str

    def __str__(self):
        return f'{self.name}'


@dataclass(frozen=True)
class User(Target):
    id: int
    name: str
    discriminator: int
    server: Optional[Server]

    def __str__(self):
        server_part = '' if self.server is None else f' on {self.server.name}'
        return f'@{self.name}#{self.discriminator}{server_part}'


@dataclass(frozen=True)
class Channel(Target):
    id: int
    name: str
    server: Optional[Server]

    def __str__(self):
        server_part = '' if self.server is None else f' on {self.server.name}'
        return f'#{self.name}{server_part}'


@dataclass(frozen=True)
class Topic(Target):
    """
    Special target for building models of sentences related to a
    certain keyword, e.g. 'Genshin Impact'
    """
    name: str
    server: Optional[Server]
    keywords: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Picture:
    """
    Data about a picture uploaded to Discord
    """
    # todo: use sqlalchemy ORM, replace *_id columns with foreign keys
    id: int
    url: str
    msg: str  # message in the post with the picture, if any
    time: datetime
    uploader_id: int
    channel_id: int
    server_id: int
    sfw: bool

    # no idea why this is not working by default
    def __eq__(self, other):
        if not isinstance(other, Picture):
            return False
        return self.id == other.id and self.url == other.url and self.msg == other.msg and \
               self.time == other.time and self.uploader_id == other.uploader_id and \
               self.channel_id == other.channel_id and self.server_id == other.server_id and \
               self.sfw == other.sfw


@dataclass
class Message:
    server: Optional[Server]
    user: User
    channel: Channel
    text: str
    created_at: datetime
    pictures: list[Picture] = field(default_factory=list)
