from typing import Optional

from discord.ext.commands.context import Context as DiscordContext

from cheems.types import Server, Target, User, Channel


def extract_target(ctx: DiscordContext) -> Optional[Target]:
    """
    Returns the first applicable target from the Discord message.
    E.g. if it's a mentioned @user or #channel, returns that user or channel.
    """
    server = Server(id=ctx.guild.id, name=ctx.guild.name)
    msg = ctx.message
    if len(msg.mentions) > 0:
        d_user = msg.mentions[0]
        return User(id=d_user.id, name=d_user.name, discriminator=d_user.discriminator, server=server)

    if len(msg.channel_mentions) > 0:
        d_channel = msg.channel_mentions[0]
        return Channel(id=d_channel.id, name=d_channel.name, server=server)

    return None
