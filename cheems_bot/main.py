import logging

import config
from discord.ext import commands

# Initialize Bot and Denote The Command Prefix
bot = commands.Bot(command_prefix="!")
logger = logging.getLogger('cheems_bot')


# Runs when Bot Successfully Connects
@bot.event
async def on_ready():
    logger.info(f'{bot.user} successfully logged in!')


try:
    bot.run(config.discord_token)
except Exception:
    logger.exception("Couldn't run bot")
