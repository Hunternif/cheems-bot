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
`.che` - генерирует рандомную фразу из всего сервера.
`.che #канал` - генерирует рандомную фразу из канала.
`.che @никнейм` или `.che никнейм` - генерирует рандомную фразу из сообщений человека.
`.help4` - показывает эту справку.
'''.strip(),
            color=0xd19d2e
        )
        await ctx.send(embed=embed)
