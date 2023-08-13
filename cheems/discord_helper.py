import re
from datetime import datetime, timezone
from typing import Optional

from discord import Message as DiscordMessage, Guild
from discord.ext.commands.context import Context as DiscordContext, Context
from discord.user import BaseUser

from cheems.config import is_channel_sfw
from cheems.pictures import Picture
from cheems.targets import Server, Target, User, Channel, Message

# Discord epoch time
EPOCH = datetime(year=2015, month=1, day=1, tzinfo=timezone.utc)


def map_server(guild: Optional[Guild]) -> Optional[Server]:
    if guild is None:
        return None
    return Server(id=int(guild.id), name=str(guild.name))


def map_user(m: BaseUser, server: Optional[Server]) -> User:
    return User(
        id=int(m.id),
        name=str(m.name),
        discriminator=int(m.discriminator),
        server=server,
    )


def map_channel(ch) -> Channel:
    if hasattr(ch, 'name') and hasattr(ch, 'guild'):
        server = map_server(ch.guild)
        return Channel(id=int(ch.id), name=str(ch.name), server=server)
    else:
        return Channel(id=int(ch.id), name=str(ch), server=None)


def _simplify_word(word: str) -> str:
    """Returns a version of the word for comparison, e.g. stripped of emoji."""
    word = word.strip().lower()
    return re.sub(r'\W+', '', word)


def extract_target(ctx: DiscordContext) -> Target:
    """
    Returns the first applicable target from the Discord message.
    E.g. if it's a mentioned @user or #channel, returns that user or channel.
    """
    server = map_server(ctx.guild)
    msg = ctx.message
    for m in msg.mentions:
        if m.id == ctx.me.id:
            # don't target itself
            continue
        return map_user(m, server)

    # try to find a user without a mention:
    # text: str = msg.system_content or ''
    # words = re.split(r'\s+', text)
    # if len(words) > 1:
    #     # assuming the first word is the command,
    #     # and the 1st argument is the mention
    #     maybe_mention = _simplify_word(words[1])
    #     for target in models_xml.models_by_server_id.get(server.id, {}).keys():
    #         if hasattr(target, 'name'):
    #             target_name = _simplify_word(target.name)
    #             if target_name == maybe_mention:
    #                 return target

    # try to find channel mentions:
    if len(msg.channel_mentions) > 0:
        return map_channel(msg.channel_mentions[0])

    # no mentions, use current channel:
    return server


def map_message(msg: DiscordMessage) -> Message:
    """Converts Discord message to domain type"""
    server = map_server(msg.guild) if hasattr(msg, 'guild') else None
    user = map_user(msg.author, server)
    channel = map_channel(msg.channel)
    if server is None:
        sfw = True
    else:
        sfw = is_channel_sfw(server.name, channel.name)
    text = msg.system_content or ''  # use raw content to include mentions
    created_at = msg.created_at
    pics = []
    for att in msg.attachments:
        if (att.width or 0) > 0:
            if (att.filename or '').startswith('SPOILER'):
                sfw = False
            pics.append(Picture(
                att.id,
                att.url,
                msg.clean_content,
                created_at,
                user.id,
                channel.id,
                server.id,
                sfw
            ))
    return Message(server, user, channel, text, created_at, pictures=pics)


def format_mention(target: Target) -> str:
    """Returns the Discord mention of this target"""
    if isinstance(target, User):
        return f'<@{target.id}>'
    elif isinstance(target, Channel):
        return f'<#{target.id}>'
    else:
        return ''


def get_command_argument(ctx: Context) -> str:
    """Strip the command name from message text."""
    text: str = ctx.message.system_content or ''
    if ctx.command is not None:
        text = text.replace(f'{ctx.prefix}{ctx.command.name}', '', 1).strip()
    return text


def remove_mention(text: str, target: Target) -> str:
    """Removes both ids <@123> and name of the target"""
    mention = format_mention(target)
    if len(mention) > 0:
        text = text.replace(f'{mention}', '').strip()
    if hasattr(target, 'name'):
        target_name = target.name.lower()
        if text.lower().startswith(target_name):
            text = text[len(target_name):].strip()
    return text
