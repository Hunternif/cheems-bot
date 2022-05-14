import config
from discord.ext import commands

# Initialize Bot and Denote The Command Prefix
bot = commands.Bot(command_prefix="!")


# Runs when Bot Successfully Connects
@bot.event
async def on_ready():
    print(f'{bot.user} successfully logged in!')


bot.run(config.discord_token)
