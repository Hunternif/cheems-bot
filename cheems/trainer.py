import asyncio
import logging
from datetime import datetime, timedelta, timezone

from discord import TextChannel
from discord.ext.commands import Bot

from cheems import pictures
from cheems.config import config, is_name_allowed, is_message_id_allowed, \
    is_name_special
from cheems.discord_helper import map_channel, map_message, EPOCH
from cheems.markov import models_xml
from cheems.markov.markov import train_models_on_sentence
from cheems.markov.model import Model
from cheems.targets import Message

logger = logging.getLogger('trainer')


class CheemsTrainer:
    bot: Bot
    save_period = timedelta(minutes=2)
    unsaved_models = set()
    unsaved_picture_count = 0

    def __init__(self, bot: Bot):
        self.bot = bot

    async def train(self):
        self.bot.loop.create_task(self._save_models_periodic())
        for guild in self.bot.guilds:
            for discord_channel in guild.channels:
                if isinstance(discord_channel, TextChannel):
                    self.bot.loop.create_task(
                        self.continuously_update_models_from_channel(discord_channel)
                    )

    async def continuously_update_models_from_channel(self, discord_channel: TextChannel):
        """
        Recursively runs `update_models_from_channel` until there are no more messages
        """
        ch = map_channel(discord_channel)
        ch_model = models_xml.get_or_create_model(ch)
        server_model = models_xml.get_or_create_model(ch.server)
        # find the earliest time from which to update
        # TODO: is this time calculation correct, e.g. if I'm training deer-gacha separately?
        from_time = min(server_model.to_time, ch_model.to_time)
        num_fetched = await asyncio.create_task(
            self.update_models_from_channel(discord_channel, from_time)
        )
        if num_fetched > 0:
            await asyncio.sleep(config['training'].get('wait_sec', 0))
            await asyncio.create_task(
                self.continuously_update_models_from_channel(discord_channel)
            )

    async def update_models_from_channel(
            self,
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
        channel_is_special = is_name_special(channel_config, ch.name)

        count = 0
        try:
            history = discord_channel.history(
                limit=config['training']['message_limit'],
                after=from_time,
                oldest_first=True,
            )
            async for discord_message in history:
                if channel_is_special:
                    models = [ch_model]
                else:
                    models = [ch_model, server_model]

                msg = map_message(discord_message)
                if msg.user.id != self.bot.user.id and is_name_allowed(user_config, msg.user.name) \
                        and is_message_id_allowed(server_config, discord_message.id):
                    # TODO: continuing user's model from last iteration doesn't work: the model is overwritten!
                    user_model = models_xml.get_or_create_model(msg.user)

                    if is_name_special(user_config, msg.user.name):
                        #  TODO: update channel 'to_time' anyway!
                        models = [user_model]
                    elif not channel_is_special:
                        models.append(user_model)

                    self.train_models(models, msg)
                    for model in models:
                        self.unsaved_models.add(model)
                else:
                    # don't train the models, but update their timestamps
                    for model in models:
                        if model.to_time < msg.created_at:
                            model.to_time = msg.created_at
                            model.updated_time = datetime.now(tz=timezone.utc)
                            self.unsaved_models.add(model)
                count += 1
        except Exception as e:
            logger.exception(f'Error parsing channel {ch}: {e}')
            return count
        if count > 0:
            logger.info(f'Fetched {count} messages from {ch}')
        else:
            logger.info(f'Finished fetching {ch.name}')
            models_xml.save_model(ch_model)
            self.unsaved_models.discard(ch_model)
        return count

    def train_models(self, models: list[Model], msg: Message):
        """
        Update content and time of models based on the message.
        """
        models_data = [m.data for m in models]
        train_models_on_sentence(models_data, msg.text)
        for model in models:
            if model.from_time == EPOCH:
                model.from_time = msg.created_at
            if model.from_time > msg.created_at:
                model.from_time = msg.created_at
            if model.to_time < msg.created_at:
                model.to_time = msg.created_at
            model.updated_time = datetime.now(tz=timezone.utc)
        # also save images
        # todo: use a separate date count for pictures?
        for p in msg.pictures:
            pictures.save_pic(p)
            self.unsaved_picture_count += 1

    async def _save_models_periodic(self):
        """save all unsaved models periodically."""
        while True:
            await asyncio.sleep(self.save_period.seconds)
            logger.info('Saving all models...')
            self._save_models()

    def _save_models(self):
        """save all unsaved models"""
        unsaved_count = len(self.unsaved_models)
        while len(self.unsaved_models) > 0:
            model = self.unsaved_models.pop()
            models_xml.save_model(model)
        logger.info(f'Saved {unsaved_count} models')
        pictures.save_all()
        logger.info(f'Saved {self.unsaved_picture_count} pictures')
        self.unsaved_picture_count = 0