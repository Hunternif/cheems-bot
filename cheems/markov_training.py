import asyncio
import logging
from datetime import datetime

from discord import TextChannel

from cheems.config import config, is_name_allowed
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
        for discord_channel in guild.channels:
            if isinstance(discord_channel, TextChannel):
                await asyncio.create_task(
                    continuously_update_models_from_channel(discord_channel)
                )


async def continuously_update_models_from_channel(discord_channel: TextChannel):
    """
    Recursively runs `update_models_from_channel` until there are no more messages
    """
    ch = map_channel(discord_channel)
    ch_model = models_xml.get_or_create_model(ch)
    server_model = models_xml.get_or_create_model(ch.server)
    # find the earliest time from which to update
    from_time = min(server_model.to_time, ch_model.to_time)
    num_fetched = await asyncio.create_task(
        update_models_from_channel(discord_channel, from_time)
    )
    if num_fetched > 0:
        await asyncio.sleep(config['training'].get('wait_sec', 0))
        await asyncio.create_task(
            continuously_update_models_from_channel(discord_channel)
        )
    else:
        logger.info(f'Finished fetching {ch.name}')


async def update_models_from_channel(
        discord_channel: TextChannel,
        from_time: datetime
) -> int:
    """
    Fetches a batch of messages from the channel after the given time,
    and updates all models relevant to that server, channel, user etc.
    :return: the number of messages fetched
    """
    ch = map_channel(discord_channel)
    ch_model = models_xml.get_or_create_model(ch)
    server_model = models_xml.get_or_create_model(ch.server)

    # check blocklists and allowlists in config:
    server_config = config.get('training', {}).get('servers', {}).get(ch.server.name, {})
    channel_config = server_config.get('channels', {})
    user_config = server_config.get('users', {})
    if not is_name_allowed(channel_config, ch.name):
        return 0

    count = 0
    try:
        history = discord_channel.history(
            limit=config['training']['message_limit'],
            after=from_time,
            oldest_first=True,
        )
        async for discord_message in history:
            msg = map_message(discord_message)
            user_model = models_xml.get_or_create_model(msg.user)
            models = [ch_model, server_model]
            if is_name_allowed(user_config, msg.user.name):
                models.append(user_model)
            train_and_save_models(models, msg)
            count += 1
    except Exception as e:
        logger.exception(f'Error parsing channel {ch}: {e}')
    logger.info(f'Fetched {count} messages from {ch}')
    return count


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
