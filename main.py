import asyncio
import logging

from discord import Intents
from discord.ext.commands import Context

from cheems.pics_cog import PicsCog
from cheems.config import config
from discord.ext import commands

from cheems.help_cog import HelpCog
from cheems.markov import models_xml
from cheems.markov_cog import MarkovCog
from cheems.proactive_markov_cog import ProactiveMarkovCog
from cheems.proactive_react_cog import ProactiveReactCog

logger = logging.getLogger('cheems')
models_xml.load_models()

intents = Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)


# Runs when Bot Successfully Connects
@bot.event
async def on_ready():
    logger.info(f'{bot.user} successfully logged in!')


@bot.event
async def on_command_error(ctx: Context, error):
    # don't log errors for commands from other bots
    if ctx.cog is not None:
        logger.error(f'{ctx.cog.qualified_name} error: {error}')


async def main():
    bot.remove_command('help')
    async with bot:
        await bot.add_cog(MarkovCog(bot))
        await bot.add_cog(ProactiveMarkovCog(bot))
        await bot.add_cog(ProactiveReactCog(bot))
        await bot.add_cog(HelpCog(bot))
        await bot.add_cog(PicsCog(bot))
        await bot.start(config['discord_token'])


try:
    asyncio.run(main())
except Exception:
    logger.exception("Couldn't run bot")
