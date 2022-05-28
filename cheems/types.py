from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# Domain classes for modelling Discord interactions


@dataclass
class Target:
    """
    Base class for a Discord entity associated with a Model.
    E.g. if a Model models speech patterns of a user, this user is the target.
    """
    id: int
    name: str

    @property
    def server_id(self) -> int:
        return self.server.id if hasattr(self, 'server') else 0


@dataclass
class Server(Target):
    def __str__(self):
        return f'{self.name}'


@dataclass
class User(Target):
    discriminator: int
    server: Optional[Server]

    def __str__(self):
        server_part = '' if self.server is None else f' on {self.server.name}'
        return f'@{self.name}#{self.discriminator}{server_part}'


@dataclass
class Channel(Target):
    server: Optional[Server]

    def __str__(self):
        server_part = '' if self.server is None else f' on {self.server.name}'
        return f'#{self.name}{server_part}'


@dataclass
class Message:
    server: Optional[Server]
    user: User
    channel: Channel
    text: str
    created_at: datetime
