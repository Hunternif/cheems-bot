import logging

from discord.ext import commands
from discord.ext.commands import Bot, Context

from cheems.discord_helper import extract_target

logger = logging.getLogger(__name__)


class TextGenCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def che(self, ctx: Context):
        target = extract_target(ctx)
        logger.info(f'cheemsburger {target}')
