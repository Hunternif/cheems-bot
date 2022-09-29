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
`.cho @никнейм/#канал фраза` - генерирует продолжение фразы словами человека/канала.
`.ask вопрос` - генерирует ответ по последнему слову.
`.ask @никнейм/#канал вопрос` - генерирует ответ по последнему слову словами человека/канала.
`.pic` - постит рандомную картинку.
`.pic @никнейм/#канал фраза` - постит рандомную картинку от человека/из канала.
`.pic_nsfw` - только NSFW картинки ( ͡° ͜ʖ ͡°)
`.pic_any` - всякие картинки
`.help4` - показывает эту справку.

Если ответить на сообщение бота, это работает как `.ask`. Меншон бота работает как `.cho`.
'''.strip(),
            color=0xd19d2e
        )
        await ctx.send(embed=embed)
