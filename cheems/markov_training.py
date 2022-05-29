import asyncio
import logging
from datetime import datetime, timedelta

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


# todo: use mutex
last_save_time: datetime = datetime.now()
save_period = timedelta(minutes=15)
unsaved_models = set()


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
    _save_unsaved_models()


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
            models = [ch_model, server_model]
            msg = map_message(discord_message)
            user_model = models_xml.get_or_create_model(msg.user)
            if is_name_allowed(user_config, msg.user.name):
                models.append(user_model)
            train_models(models, msg)
            for model in models:
                unsaved_models.add(model)
            count += 1
    except Exception as e:
        logger.exception(f'Error parsing channel {ch}: {e}')
    if count > 0:
        logger.info(f'Fetched {count} messages from {ch}')
    else:
        logger.info(f'Finished fetching {ch.name}')
        models_xml.save_model(ch_model)
        unsaved_models.remove(ch_model)
    return count


def train_models(models: list[Model], msg: Message):
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


def _save_unsaved_models():
    # save every 15 minutes:
    global last_save_time
    if datetime.now() > (last_save_time + save_period):
        unsaved_count = len(unsaved_models)
        while len(unsaved_models) > 0:
            model = unsaved_models.pop()
            models_xml.save_model(model)
        last_save_time = datetime.now()
        logger.info(f'Saved {unsaved_count} models')


if __name__ == '__main__':
    bot.run(config['discord_token'])
