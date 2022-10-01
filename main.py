import logging

from discord.ext.commands import Context

from cheems.pics_cog import PicsCog
from cheems.config import config
from discord.ext import commands

from cheems.help_cog import HelpCog
from cheems.markov import models_xml
from cheems.markov_cog import MarkovCog
from cheems.proactive_markov_cog import ProactiveMarkovCog

logger = logging.getLogger('cheems')
models_xml.load_models()
bot = commands.Bot(command_prefix='.')
bot.remove_command('help')
bot.add_cog(MarkovCog(bot))
bot.add_cog(ProactiveMarkovCog(bot))
bot.add_cog(HelpCog(bot))
bot.add_cog(PicsCog(bot))


# Runs when Bot Successfully Connects
@bot.event
async def on_ready():
    logger.info(f'{bot.user} successfully logged in!')


@bot.event
async def on_command_error(ctx: Context, error):
    # don't log errors for commands from other bots
    if ctx.cog is not None:
        logger.error(f'{ctx.cog.qualified_name} error: {error}')


try:
    bot.run(config['discord_token'])
except Exception:
    logger.exception("Couldn't run bot")
