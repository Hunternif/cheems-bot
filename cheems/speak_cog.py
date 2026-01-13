import logging
from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import Bot, Context

logger = logging.getLogger(__name__)


class SpeakCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def speak(self, ctx: Context):
        """`.speak #channel message` - Make the bot post your message to the specified channel."""
        # Parse the channel from the message
        channel = await self._extract_channel(ctx)
        if channel is None:
            await ctx.send("Please specify a valid channel, e.g. `.speak #channel-name your message here`")
            return

        # Get the message content after the channel mention
        message_content = self._get_message_after_channel(ctx)
        
        # Check if there's actually a message to send
        if not message_content and not ctx.message.attachments:
            await ctx.send("Please provide a message to send!")
            return

        try:
            # Send the message to the target channel
            files = []
            if ctx.message.attachments:
                # Download and prepare attachments for forwarding
                for attachment in ctx.message.attachments:
                    file = await attachment.to_file()
                    files.append(file)
            
            if files:
                await channel.send(content=message_content if message_content else None, files=files)
            else:
                await channel.send(message_content)
            
            # Confirm to the user
            await ctx.message.add_reaction('✅')
            logger.info(f'{ctx.author.name} made bot speak in #{channel.name}: {message_content}')
            
        except discord.Forbidden:
            await ctx.send(f"I don't have permission to post in {channel.mention}")
            logger.warning(f'{ctx.author.name} tried to speak in #{channel.name} but bot lacks permissions')
        except Exception as e:
            await ctx.send(f"Failed to send message: {e}")
            logger.error(f'Error sending message to #{channel.name}: {e}')

    async def _extract_channel(self, ctx: Context) -> Optional[discord.TextChannel]:
        """Extract channel mention from the command."""
        # Check for channel mentions
        if ctx.message.channel_mentions:
            return ctx.message.channel_mentions[0]
        
        # Try to parse channel ID from the message
        parts = ctx.message.content.split(maxsplit=2)
        if len(parts) >= 2:
            channel_str = parts[1]
            # Remove # if present
            if channel_str.startswith('#'):
                channel_str = channel_str[1:]
            
            # Try to find channel by name in the current guild
            if ctx.guild:
                for channel in ctx.guild.text_channels:
                    if channel.name == channel_str or str(channel.id) == channel_str:
                        return channel
        
        return None

    def _get_message_after_channel(self, ctx: Context) -> str:
        """Get the message content after the channel specification."""
        parts = ctx.message.content.split(maxsplit=2)
        if len(parts) >= 3:
            return parts[2]
        return ""
