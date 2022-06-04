import logging

from discord.ext import commands
from discord.ext.commands import Bot, Context

from cheems import pictures
from cheems.discord_helper import extract_target, get_command_argument, remove_mention
from cheems.targets import User, Channel, Server

logger = logging.getLogger(__name__)


class PicsCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def pic(self, ctx: Context):
        """`.pic @user/#channel` post a random picture from the given target."""
        target = extract_target(ctx)
        prompt = get_command_argument(ctx)
        logger.info(f'{ctx.author.name} requested pic from {target}: {prompt}')
        prompt = remove_mention(prompt, target)
        pics = []
        if isinstance(target, User):
            pics = pictures.get_pics_where(
                server_id=target.server_id,
                uploader_id=target.id,
                word=prompt,
                random=True,
                limit=1
            )
        elif isinstance(target, Channel):
            pics = pictures.get_pics_where(
                server_id=target.server_id,
                channel_id=target.id,
                word=prompt,
                random=True,
                limit=1
            )
        elif isinstance(target, Server):
            pics = pictures.get_pics_where(
                server_id=target.id,
                word=prompt,
                random=True,
                limit=1
            )
        if len(pics) > 0:
            await ctx.send(pics[0].url)
