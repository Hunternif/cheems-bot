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
    server: Server

    def __attrs_post_init__(self):
        self.server_id = self.server.id

    def __str__(self):
        return f'@{self.name}#{self.discriminator}'


@define
class Channel(Target):
    server: Server

    def __attrs_post_init__(self):
        self.server_id = self.server.id

    def __str__(self):
        return f'#{self.name}'


@define
class Message:
    server: Server
    user: User
    channel: Channel
    text: str
