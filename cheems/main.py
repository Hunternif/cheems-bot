import logging

import config
from discord.ext import commands
from discord.ext.commands.context import Context as DiscordContext
from cheems.discord_helper import extract_target

# Initialize Bot and Denote The Command Prefix
bot = commands.Bot(command_prefix=".")
logger = logging.getLogger('cheems')


# Runs when Bot Successfully Connects
@bot.event
async def on_ready():
    logger.info(f'{bot.user} successfully logged in!')


@bot.command()
async def che(ctx: DiscordContext):
    target = extract_target(ctx)
    logger.info(f'cheemsburger {target}')


@bot.event
async def on_command_error(ctx, error):
    # don't log errors for commands from other bots
    pass


try:
    bot.run(config.discord_token)
except Exception:
    logger.exception("Couldn't run bot")
