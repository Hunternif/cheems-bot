from attr import define


# Domain classes for modelling Discord interactions

@define
class Server:
    id: int
    name: str


@define
class Target:
    id: int
    name: str
    server: Server


@define
class User(Target):
    discriminator: int

    def __str__(self):
        return f'@{self.name}#{self.discriminator}'


@define
class Channel(Target):
    def __str__(self):
        return f'#{self.name}'
