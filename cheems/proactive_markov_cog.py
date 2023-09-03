import logging

from discord import Message
from discord.ext import commands
from discord.ext.commands import Bot

from cheems.config import config
from cheems.discord_helper import map_message
from cheems.markov_cog import reply_back

logger = logging.getLogger(__name__)


class ProactiveMarkovCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.messagesSinceBotByChannel: dict[int, int] = {}
        self.config = config.get('proactive_reply', {})
        self.period_msgs = int(self.config.get('period_msgs', 100))

    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        """
        If enough messages have been sent since the bot's message in this channel,
        respond
        """
        if msg.author.id == self.bot.user.id:
            self.messagesSinceBotByChannel[msg.channel.id] = 0
        else:
            m = map_message(msg)
            if not config.is_feature_allowed('proactive_reply', m.channel):
                return
            count = self.messagesSinceBotByChannel.get(msg.channel.id, 0)
            count += 1
            self.messagesSinceBotByChannel[msg.channel.id] = count
            if count >= self.period_msgs:
                self.messagesSinceBotByChannel[msg.channel.id] = 0
                logger.info(f'Proactively replying to message: {msg.system_content}')
                await reply_back(msg, use_channel=True)
