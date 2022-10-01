from discord import Message
from discord.ext import commands
from discord.ext.commands import Bot

from cheems.config import config, is_name_allowed
from cheems.discord_helper import map_message
from cheems.markov_cog import reply_back


class ProactiveMarkovCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.messagesSinceBotByChannel: dict[int, int] = {}
        self.config = config.get('proactive_reply', {})
        self.period_msgs = self.config.get('period_msgs', 100)

    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        """
        If enough messages have been sent since the bot's message in this channel,
        respond
        """
        if msg.author.id == self.bot.user.id:
            self.messagesSinceBotByChannel[msg.channel.id] = 0
        else:
            if not self._is_channel_allowed(msg):
                return
            count = self.messagesSinceBotByChannel.get(msg.channel.id, 0)
            count += 1
            self.messagesSinceBotByChannel[msg.channel.id] = count
            if count >= self.period_msgs:
                self.messagesSinceBotByChannel[msg.channel.id] = 0
                await reply_back(msg)

    def _is_channel_allowed(self, msg: Message):
        m = map_message(msg)
        server_config = self.config.get('servers', {}).get(m.server.name, None)
        if server_config is None:
            return False
        channel_config = server_config.get('channels', {})
        return is_name_allowed(channel_config, m.channel.name)
