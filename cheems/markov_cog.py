import logging

from discord.ext import commands
from discord.ext.commands import Bot, Context

from cheems.discord_helper import extract_target
from cheems.markov import models_xml
from cheems.markov.markov import markov_chain

logger = logging.getLogger(__name__)


class MarkovCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def che(self, ctx: Context):
        target = extract_target(ctx)
        logger.info(f'{ctx.author.name} cheemsed {target}')
        model = models_xml.get_model(target)
        if model is not None:
            await ctx.send(markov_chain(model.data))
