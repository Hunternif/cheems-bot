import logging
from typing import Optional

from discord.ext import commands
from discord.ext.commands import Bot, Context

from cheems import pictures
from cheems.discord_helper import extract_target, get_command_argument, remove_mention
from cheems.targets import User, Channel, Server, Picture

logger = logging.getLogger(__name__)


class PicsCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def pic(self, ctx: Context):
        """`.pic @user/#channel` post a random picture from the given target."""
        await _pic(ctx, sfw=True)

    @commands.command()
    async def pic_nsfw(self, ctx: Context):
        """Post a random NSFW picture. Uses target"""
        await _pic(ctx, sfw=False)

    @commands.command()
    async def pic_any(self, ctx: Context):
        """Post a random picture, either SFW or NSFW. Uses target"""
        await _pic(ctx)


async def _pic(ctx: Context, sfw: bool = None):
    target = extract_target(ctx)
    prompt = get_command_argument(ctx)
    if sfw is None:
        sfw_str = ''
    elif sfw:
        sfw_str = 'SFW '
    else:
        sfw_str = 'NSFW '
    logger.info(f'{ctx.author.name} requested {sfw_str}pic from {target}: {prompt}')
    prompt = remove_mention(prompt, target)
    if isinstance(target, User):
        pic = _get_random_pic(
            server_id=target.server_id,
            uploader_id=target.id,
            word=prompt,
            sfw=sfw,
        )
    elif isinstance(target, Channel):
        pic = _get_random_pic(
            server_id=target.server_id,
            channel_id=target.id,
            word=prompt,
            sfw=sfw,
        )
    elif isinstance(target, Server):
        pic = _get_random_pic(
            server_id=target.id,
            word=prompt,
            sfw=sfw,
        )
    else:
        pic = None
    if pic is not None:
        url = pic.url
        if not pic.sfw:
            url = f'|| {url} ||'
        await ctx.send(url)


def _get_random_pic(
        uploader_id: int = None,
        channel_id: int = None,
        server_id: int = None,
        word: str = None,
        sfw: bool = None,
) -> Optional[Picture]:
    """
    Returns 1 random pic for the given criteria.
    If it fails to find with a prompt, drops the prompt.
    """
    pics = pictures.get_pics_where(
        uploader_id=uploader_id,
        channel_id=channel_id,
        server_id=server_id,
        word=word,
        sfw=sfw,
        random=True,
        limit=1
    )
    if len(pics) <= 0:
        pics = pictures.get_pics_where(
            uploader_id=uploader_id,
            channel_id=channel_id,
            server_id=server_id,
            word=None,
            sfw=sfw,
            random=True,
            limit=1
        )
    if len(pics) > 0:
        return pics[0]
    return None
