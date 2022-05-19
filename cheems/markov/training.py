import asyncio
import logging
from datetime import datetime

from discord import TextChannel

from cheems.config import config
from discord.ext import commands

from cheems.discord_helper import map_channel, map_message
from cheems.markov import models_xml

logger = logging.getLogger('training')
models_xml.load_models()
bot = commands.Bot(command_prefix='.')
bot.remove_command('help')


@bot.event
async def on_ready():
    logger.info(f'{bot.user} successfully logged in for training!')
    await train()


async def train():
    for guild in bot.guilds:
        for discord_channel in guild.channels:
            if isinstance(discord_channel, TextChannel):
                ch = map_channel(discord_channel)
                ch_model = models_xml.get_or_create_model(ch)
                asyncio.create_task(update_model(discord_channel, ch_model.to_time))


async def update_model(discord_channel: TextChannel, after: datetime):
    history = discord_channel.history(
        limit=config['training']['message_limit'],
        after=after,
        oldest_first=True,
    )
    ch = map_channel(discord_channel)
    ch_model = models_xml.get_or_create_model(ch)
    count = 0
    async for discord_message in history:
        msg = map_message(discord_message)
        logger.info(f'{msg.user}: {msg.text}')
        count += 1
    logger.info(f'Fetched {count} messages from {ch}')


if __name__ == '__main__':
    bot.run(config['discord_token'])
