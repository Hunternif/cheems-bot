import logging

from discord import Message
from discord.ext import commands
from discord.ext.commands import Bot, Context

from cheems.config import config
from cheems.discord_helper import extract_target, map_message, map_server
from cheems.markov import models_xml
from cheems.markov.markov import markov_chain, canonical_form, strip_punctuation
from cheems.markov.model import ModelData
from cheems.types import Server

logger = logging.getLogger(__name__)
markov_retry_hard_limit = 100


class MarkovCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def che(self, ctx: Context):
        """`.che @user/#channel` generate markov chain"""
        target = extract_target(ctx)
        logger.info(f'{ctx.author.name} cheemsed {target}')
        model = models_xml.get_model(target)
        if model is not None:
            chain = markov_chain(model.data)
            if isinstance(target, Server):
                text = chain
            elif hasattr(target, 'name'):
                text = f'{target.name}: {chain}'
            else:
                text = chain
            await ctx.send(text)
            await ctx.message.delete()

    @commands.command()
    async def cho(self, ctx: Context):
        """`.cho prompt` generate markov chain from prompt"""
        msg = map_message(ctx.message)
        prompt = msg.text.replace('.cho', '').strip()
        logger.info(f'{ctx.author.name} chomsed {prompt}')

        server = map_server(ctx.guild)
        response = _continue_prompt(server, prompt)
        if len(response) > 0:
            await ctx.send(response)
            await ctx.message.delete()

    @commands.command()
    async def ask(self, ctx: Context):
        """
        `.ask prompt` will try to reply to the prompt's last word.
        Tries to use the mentioned target too.
        """
        target = extract_target(ctx)
        msg = map_message(ctx.message)
        prompt = msg.text.replace('.ask', '').strip()
        logger.info(f'{ctx.author.name} asked {target}: {prompt}')

        last_word = canonical_form(prompt.split(' ')[-1])
        model = models_xml.get_model(target)
        if model is None:
            return
        response = _markov_chain_with_retry(model.data, last_word)
        if len(response) > 0:
            await ctx.message.reply(response)

    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        """If someone replies to the bot's message, continue the conversation"""
        if msg.author.id == self.bot.user.id or msg.is_system():
            return
        # check if it's a reply to this bot
        if msg.reference is not None and \
                msg.reference.resolved.author.id == self.bot.user.id:
            await _reply_back(msg)
            return
        # check if it's a mention of this bot. It acts like `cho`.
        m = map_message(msg)
        for mention in msg.mentions:
            if mention.id == self.bot.user.id:
                prompt = m.text.replace(f'<@{self.bot.user.id}>', '').strip()
                logger.info(f'{msg.author.name} chomsed {prompt}')
                response = _continue_prompt(m.server, prompt)
                if len(response) > 0:
                    await msg.channel.send(response)
                    await msg.delete()


def _continue_prompt(server: Server, prompt: str) -> str:
    """Returns empty string if could not continue."""
    model = models_xml.get_model(server)
    if model is None:
        return ''
    return _markov_chain_with_retry(model.data, prompt)


async def _reply_back(msg: Message):
    """Reply to the message by continuing the Markov chain from the last word."""
    m = map_message(msg)
    if m.server is None:
        return  # can't reply outside of server
    logger.info(f'{msg.author.name} replied {m.text}')
    last_word = canonical_form(m.text.split(' ')[-1])
    model = models_xml.get_model(m.server)
    if model is None:
        return
    response = _markov_chain_with_retry(model.data, last_word)
    if len(response) > 0:
        await msg.reply(response)


def _markov_chain_with_retry(data: ModelData, prompt: str) -> str:
    """
    Reruns markov chain multiple times if it fails to do attempts.
    Falls back to running without the prompt, and finally
    falls back to empty string.
    """
    attempt_count = 0
    limit = min(config.get('markov_retry_limit', markov_retry_hard_limit), markov_retry_hard_limit)
    while attempt_count < limit:
        chain = markov_chain(data, start=prompt)
        if strip_punctuation(chain) != strip_punctuation(prompt):
            return chain
        attempt_count += 1
        logger.info(f'Retry {str(attempt_count)} for prompt {prompt}')
    # retry without the phrase
    chain = markov_chain(data)
    if strip_punctuation(chain) == strip_punctuation(prompt):
        return ''
    return f'{prompt} {chain}'
