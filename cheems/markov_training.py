import asyncio
import logging
from datetime import datetime

from discord import TextChannel

from cheems.config import config
from discord.ext import commands

from cheems.discord_helper import map_channel, map_message, map_server
from cheems.markov import models_xml
from cheems.markov.markov import train_models_on_sentence
from cheems.markov.model import Model
from cheems.types import Message

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
        server_model = models_xml.get_or_create_model(map_server(guild))
        for discord_channel in guild.channels:
            if isinstance(discord_channel, TextChannel):
                ch_model = models_xml.get_or_create_model(map_channel(discord_channel))
                # find the earliest time from which to update
                from_time = min(server_model.to_time, ch_model.to_time)
                asyncio.create_task(update_models_from_channel(discord_channel, from_time))


async def update_models_from_channel(
        discord_channel: TextChannel,
        from_time: datetime
):
    """
    Fetches a batch of messages from the channel after the given time,
    and updates all models relevant to that server, channel, user etc.
    """
    history = discord_channel.history(
        limit=config['training']['message_limit'],
        after=from_time,
        oldest_first=True,
    )
    ch = map_channel(discord_channel)
    ch_model = models_xml.get_or_create_model(ch)
    server_model = models_xml.get_or_create_model(ch.server)
    count = 0
    try:
        async for discord_message in history:
            msg = map_message(discord_message)
            user_model = models_xml.get_or_create_model(msg.user)
            train_and_save_models([ch_model, server_model, user_model], msg)
            count += 1
    except Exception as e:
        logger.exception(f'Error parsing channel {ch}: {e}')
    logger.info(f'Fetched {count} messages from {ch}')


def train_and_save_models(models: list[Model], msg: Message):
    """
    Update content and time of models based on the message.
    """
    models_data = [m.data for m in models]
    train_models_on_sentence(models_data, msg.text)
    for model in models:
        if model.from_time == models_xml.EPOCH:
            model.from_time = msg.created_at
        if model.to_time < msg.created_at:
            model.to_time = msg.created_at
        model.updated_time = datetime.now()
        models_xml.save_model(model)


if __name__ == '__main__':
    bot.run(config['discord_token'])
