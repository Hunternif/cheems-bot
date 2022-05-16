from typing import Optional

from attr import define, field


# Domain classes for modelling Discord interactions


@define
class Target:
    id: int
    name: str
    server_id: int = field(init=False)


@define
class Server(Target):
    def __attrs_post_init__(self):
        self.server_id = self.id

    def __str__(self):
        return f'{self.name}'


@define
class User(Target):
    discriminator: int
    server: Optional[Server]

    def __attrs_post_init__(self):
        self.server_id = 0 if self.server is None else self.server.id

    def __str__(self):
        server_part = '' if self.server is None else f' on {self.server.name}'
        return f'@{self.name}#{self.discriminator}{server_part}'


@define
class Channel(Target):
    server: Optional[Server]

    def __attrs_post_init__(self):
        self.server_id = 0 if self.server is None else self.server.id

    def __str__(self):
        server_part = '' if self.server is None else f' on {self.server.name}'
        return f'#{self.name}{server_part}'


@define
class Message:
    server: Optional[Server]
    user: User
    channel: Channel
    text: str
