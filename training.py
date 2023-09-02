import asyncio
import logging

from discord import Intents
from discord.ext import commands

from cheems.config import config
from cheems.markov import models_xml
from cheems.trainer import CheemsTrainer

logger = logging.getLogger('training')
models_xml.load_models()

intents = Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)
trainer = CheemsTrainer(bot)


@bot.event
async def on_ready():
    logger.info(f'{bot.user} successfully logged in for training!')
    await trainer.train()


async def main():
    bot.remove_command('help')
    async with bot:
        await bot.start(config['discord_token'])


if __name__ == '__main__':
    asyncio.run(main())
