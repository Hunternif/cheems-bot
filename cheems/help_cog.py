import logging

import discord
from discord.ext import commands
from discord.ext.commands import Bot, Context

logger = logging.getLogger(__name__)


class HelpCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def help4(self, ctx: Context):
        embed = discord.Embed(
            title='Cheems bot',
            description='''
`.che` - генерирует рандомную фразу.
`.che @никнейм/#канал` - генерирует рандомную фразу словами человека/канала.
`.cho фраза` - генерирует продолжение фразы.
`.cho_user @никнейм/#канал фраза` - генерирует продолжение фразы словами человека/канала.
`.ask вопрос` - генерирует ответ по последнему слову.
`.ask_user @никнейм/#канал вопрос` - генерирует ответ по последнему слову словами человека/канала.
`.help4` - показывает эту справку.

Если ответить на сообщение бота, это работает как `.ask`. Меншон бота работает как `.cho`.
Чтобы использовать слова человека, но не меншонить его, можно просто написать его оригинальный дискордовский никнейм, например `.cho_user hunternif`
'''.strip(),
            color=0xd19d2e
        )
        await ctx.send(embed=embed)
