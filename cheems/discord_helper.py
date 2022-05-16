from discord import Message as DiscordMessage, Guild, Member, TextChannel
from discord.ext.commands.context import Context as DiscordContext

from cheems.types import Server, Target, User, Channel, Message


def _map_server(guild: Guild) -> Server:
    return Server(id=guild.id, name=guild.name)


def _map_user(m: Member, server: Server) -> User:
    return User(id=m.id, name=m.name, discriminator=m.discriminator, server=server)


def _map_channel(ch: TextChannel, server: Server) -> Channel:
    return Channel(id=ch.id, name=ch.name, server=server)


def extract_target(ctx: DiscordContext) -> Target:
    """
    Returns the first applicable target from the Discord message.
    E.g. if it's a mentioned @user or #channel, returns that user or channel.
    """
    server = _map_server(ctx.guild)
    msg = ctx.message
    for m in msg.mentions:
        if m.id == ctx.me.id:
            # don't target itself
            continue
        return _map_user(m, server)

    if len(msg.channel_mentions) > 0:
        return _map_channel(msg.channel_mentions[0], server)

    return server


def map_message(msg: DiscordMessage) -> Message:
    """Converts Discord message to domain type"""
    server = _map_server(msg.guild)
    user = _map_user(msg.author, server)
    channel = _map_channel(msg.channel, server)
    text = msg.clean_content
    return Message(server, user, channel, text)
