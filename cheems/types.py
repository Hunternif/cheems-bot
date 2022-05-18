from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# Domain classes for modelling Discord interactions


@dataclass
class Target:
    """Base class for the entity that a Markov model describes."""
    id: int
    name: str
    created_at: datetime
    server_id: int = field(init=False)


@dataclass
class Server(Target):
    def __post_init__(self):
        self.server_id = self.id

    def __str__(self):
        return f'{self.name}'


@dataclass
class User(Target):
    discriminator: int
    server: Optional[Server]

    def __post_init__(self):
        self.server_id = 0 if self.server is None else self.server.id

    def __str__(self):
        server_part = '' if self.server is None else f' on {self.server.name}'
        return f'@{self.name}#{self.discriminator}{server_part}'


@dataclass
class Channel(Target):
    server: Optional[Server]

    def __post_init__(self):
        self.server_id = 0 if self.server is None else self.server.id

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
