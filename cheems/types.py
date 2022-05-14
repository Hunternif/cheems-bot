from attr import define


# Domain classes for modelling Discord interactions


@define
class Target:
    id: int
    name: str


@define
class Server(Target):
    def __str__(self):
        return f'{self.name}'


@define
class User(Target):
    discriminator: int
    server: Server

    def __str__(self):
        return f'@{self.name}#{self.discriminator}'


@define
class Channel(Target):
    server: Server

    def __str__(self):
        return f'#{self.name}'
