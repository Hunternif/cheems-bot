import logging

from discord.ext.commands import Context

from cheems.config import config
from discord.ext import commands

from cheems.markov import models
from cheems.text_gen_cog import TextGenCog

logger = logging.getLogger('cheems')
models.load_models()
bot = commands.Bot(command_prefix='.')
bot.remove_command('help')
bot.add_cog(TextGenCog(bot))


# Runs when Bot Successfully Connects
@bot.event
async def on_ready():
    logger.info(f'{bot.user} successfully logged in!')


@bot.event
async def on_command_error(ctx: Context, error):
    # don't log errors for commands from other bots
    if ctx.cog is not None:
        logger.exception(f'{ctx.cog.qualified_name} error')


try:
    bot.run(config['discord_token'])
except Exception:
    logger.exception("Couldn't run bot")
