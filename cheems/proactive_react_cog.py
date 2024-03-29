import logging

from discord import Message
from discord.ext import commands
from discord.ext.commands import Bot

from cheems.config import config
from cheems.discord_helper import map_message
from cheems.reaction import reactions

logger = logging.getLogger(__name__)


class ProactiveReactCog(commands.Cog):
    """
    Adds random reaction occasionally
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.messagesSinceBotByChannel: dict[int, int] = {}
        self.config = config.get('proactive_react', {})
        self.period_msgs = int(self.config.get('period_msgs', 100))

    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        """
        If enough messages have been sent since the bot's message in this channel,
        reacts
        """
        if msg.author.id == self.bot.user.id:
            self.messagesSinceBotByChannel[msg.channel.id] = 0
        else:
            m = map_message(msg)
            if not config.is_feature_allowed('proactive_react', m.channel):
                return
            count = self.messagesSinceBotByChannel.get(msg.channel.id, 0)
            count += 1
            self.messagesSinceBotByChannel[msg.channel.id] = count
            if count >= self.period_msgs:
                self.messagesSinceBotByChannel[msg.channel.id] = 0
                logger.info(f'Proactively reacting to message: {msg.system_content}')
                await react_to(msg, use_channel=True)


async def react_to(msg: Message, use_channel: bool = True):
    """
    React to the message using the server's model.
    """
    m = map_message(msg)
    if m.server is None:
        return  # can't reply outside of server
    target = m.server
    if use_channel:
        channel_model = reactions.get_model(m.channel)
        if channel_model is not None:
            target = m.channel

    model = reactions.get_model(target)
    if model is None:
        logger.info(f'No reaction model for target {target}')
        return
    reaction = model.get_random_reaction()
    await msg.add_reaction(reaction)
