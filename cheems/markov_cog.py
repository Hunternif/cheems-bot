import logging

from discord.ext import commands
from discord.ext.commands import Bot, Context

from cheems.discord_helper import extract_target, map_message, map_server
from cheems.markov import models_xml
from cheems.markov.markov import markov_chain
from cheems.types import Server

logger = logging.getLogger(__name__)


class MarkovCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def che(self, ctx: Context):
        """`.che @user/#channel` generate markov chain"""
        target = extract_target(ctx)
        logger.info(f'{ctx.author.name} cheemsed {target}')
        model = models_xml.get_model(target)
        if model is not None:
            chain = markov_chain(model.data)
            if isinstance(target, Server):
                text = chain
            elif hasattr(target, 'name'):
                text = f'{target.name}: {chain}'
            else:
                text = chain
            await ctx.send(text)
            await ctx.message.delete()

    @commands.command()
    async def cho(self, ctx: Context):
        """`.cho prompt` generate markov chain from prompt"""
        msg = map_message(ctx.message)
        prompt = msg.text.replace('.cho', '').strip()
        logger.info(f'{ctx.author.name} chomsed {prompt}')

        server = map_server(ctx.guild)
        model = models_xml.get_model(server)
        if model is None:
            return

        chain = markov_chain(model.data, start=prompt)
        out_text = chain
        if chain.strip() == prompt.strip():
            # retry without the phrase:
            chain = markov_chain(model.data)
            out_text = f'{prompt} {chain}'
        await ctx.send(out_text)
        await ctx.message.delete()
