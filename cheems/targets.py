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


@dataclass
class Message:
    server: Optional[Server]
    user: User
    channel: Channel
    text: str
    created_at: datetime
