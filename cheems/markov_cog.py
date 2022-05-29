import logging

from discord.ext import commands
from discord.ext.commands import Bot, Context

from cheems.discord_helper import extract_target, map_message, format_mention
from cheems.markov import models_xml
from cheems.markov.markov import markov_chain
from cheems.types import Server

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
        msg = map_message(ctx.message)
        text = msg.text.replace('.cho', '').strip()
        logger.info(f'{ctx.author.name} chomsed {text}')

        target = extract_target(ctx)
        mention = format_mention(target)
        if len(mention) > 0:
            text = text.replace(f'{mention}', '').strip()

        model = models_xml.get_model(target)
        if model is None:
            return

        chain = markov_chain(model.data, start=text)
        if chain.strip() == text.strip():
            # didn't add anything new
            return
        if isinstance(target, Server):
            out_text = chain
        elif hasattr(target, 'name'):
            out_text = f'{target.name}: {chain}'
        else:
            out_text = chain
        await ctx.send(out_text)
        await ctx.message.delete()
