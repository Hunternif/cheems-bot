from discord.ext.commands.context import Context as DiscordContext

from cheems.types import Server, Target, User, Channel


def extract_target(ctx: DiscordContext) -> Target:
    """
    Returns the first applicable target from the Discord message.
    E.g. if it's a mentioned @user or #channel, returns that user or channel.
    """
    server = Server(id=ctx.guild.id, name=ctx.guild.name)
    msg = ctx.message
    for m in msg.mentions:
        if m.id == ctx.me.id:
            # don't target itself
            continue
        return User(id=m.id, name=m.name, discriminator=m.discriminator, server=server)

    if len(msg.channel_mentions) > 0:
        d_channel = msg.channel_mentions[0]
        return Channel(id=d_channel.id, name=d_channel.name, server=server)

    return server
