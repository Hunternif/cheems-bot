import asyncio
import logging
from asyncio import AbstractEventLoop, Task
from datetime import datetime, timedelta, timezone
from typing import Coroutine, Optional

from discord import TextChannel
from discord.ext.commands import Bot

from cheems import pictures
from cheems.config import config, is_name_allowed, is_message_id_allowed, \
    is_name_special
from cheems.discord_helper import map_channel, map_message, EPOCH
from cheems.markov import models_xml
from cheems.markov.markov import train_models_on_sentence
from cheems.markov.model import Model
from cheems.markov.model_xml import XmlModel
from cheems.targets import Message

logger = logging.getLogger('trainer')


class CheemsTrainer:
    bot: Bot
    loop: AbstractEventLoop
    tasks: list[Task] = []

    save_models_task: Optional[Task] = None
    '''Saving models is a long operation, so it's scheduled rarely.
    This task is updated whenever a save is scheduled.'''

    # TODO: move save_period into config
    save_period = timedelta(seconds=2)
    unsaved_models: set[XmlModel] = set()
    unsaved_picture_count = 0

    def __init__(self, bot: Bot):
        self.bot = bot
        self.loop = asyncio.get_running_loop()

    def begin_training(self):
        """
        Main method. Starts scraping all servers according to the config.
        """
        for guild in self.bot.guilds:
            for discord_channel in guild.text_channels:
                self._add_task(
                    self._continuously_update_models_from_channel(discord_channel)
                )

    async def wait_for_completion(self):
        """
        Waits until all ongoing tasks are completed, i.e. all servers and channels have been scraped.
        """
        await asyncio.wait(self.tasks)
        # the save task could have been added later:
        if self.save_models_task:
            await asyncio.wait([self.save_models_task])
        logger.info("Training complete")

    def _add_task(self, coro: Coroutine) -> Task:
        task = self.loop.create_task(coro)
        self.tasks.append(task)
        return task

    async def _continuously_update_models_from_channel(self, discord_channel: TextChannel):
        """
        Recursively runs `update_models_from_channel` until there are no more messages
        """
        ch = map_channel(discord_channel)
        ch_model = models_xml.get_or_create_model(ch)
        server_model = models_xml.get_or_create_model(ch.server)
        # find the earliest time from which to update
        # TODO: is this time calculation correct, e.g. if I'm training deer-gacha separately?
        from_time = min(server_model.to_time, ch_model.to_time)
        num_fetched = await self._add_task(
            self.update_models_from_channel(discord_channel, from_time)
        )
        if num_fetched > 0:
            await asyncio.sleep(int(config['training'].get('wait_sec', 0)))
            await self._add_task(
                self._continuously_update_models_from_channel(discord_channel)
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

        # check blocklists and allowlists in config:
        server_config = config.get('training', {}).get('servers', {}).get(ch.server.name, None)
        if server_config is None:
            return 0
        channel_config = server_config.get('channels', {})
        user_config = server_config.get('users', {})
        if not is_name_allowed(channel_config, ch.name):
            return 0
        channel_is_special = is_name_special(channel_config, ch.name)

        ch_model = models_xml.get_or_create_model(ch)
        server_model = models_xml.get_or_create_model(ch.server)
        count = 0
        try:
            history = discord_channel.history(
                limit=int(config['training']['message_limit']),
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
            self.schedule_save_all_models()
            logger.info(f'Fetched {count} messages from {ch}')
        else:
            logger.info(f'Finished fetching {ch.name}')
            # TODO: figure out when all channels have been scraped, so that
            #  we can save all models immediately
            self.save_model(ch_model)
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

    def schedule_save_all_models(self, delay_seconds: int = None):
        """Schedules saving all models, if it's not already scheduled."""
        if self.save_models_task is not None:
            return
        self.save_models_task = self._add_task(self._save_all_models_delayed(delay_seconds))

    async def _save_all_models_delayed(self, delay_seconds: int = None):
        """save all unsaved models after a delay."""
        if not delay_seconds:
            delay_seconds = self.save_period.seconds
        await asyncio.sleep(delay_seconds)
        logger.info('Saving all models...')
        unsaved_count = len(self.unsaved_models)
        while len(self.unsaved_models) > 0:
            model = self.unsaved_models.pop()
            models_xml.save_model(model)
        logger.info(f'Saved {unsaved_count} models')
        pictures.save_all()
        logger.info(f'Saved {self.unsaved_picture_count} pictures')
        self.unsaved_picture_count = 0
        self.save_models_task = None

    def save_model(self, model: XmlModel):
        logger.info(f'Saving model {model.file_path}')
        models_xml.save_model(model)
        self.unsaved_models.discard(model)
        if len(self.unsaved_models) <= 0:
            self.save_models_task.cancel()
            self.save_models_task = None
