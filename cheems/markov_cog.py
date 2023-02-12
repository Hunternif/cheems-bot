import logging

from discord import Message
from discord.ext import commands
from discord.ext.commands import Bot, Context

from cheems.config import config
from cheems.discord_helper import extract_target, map_message, format_mention,\
    get_command_argument, remove_mention
from cheems.markov import models_xml
from cheems.markov.markov import markov_chain, canonical_form, strip_punctuation,\
    get_last_word
from cheems.markov.model import Model
from cheems.targets import Server, Target, User

logger = logging.getLogger(__name__)
markov_retry_hard_limit = 100


class MarkovCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def che(self, ctx: Context):
        """`.che @user/#channel` generate markov chain"""
        target = extract_target(ctx)
        logger.info(f'{ctx.author.name} requested .che: target: {target}')
        model = models_xml.get_model(target)
        if model is not None:
            chain = _markov_chain_with_retry(model)
            if isinstance(target, Server):
                text = chain
            elif hasattr(target, 'name'):
                text = f'{target.name}: {chain}'
            else:
                text = chain
            await ctx.send(text)
            # await ctx.message.delete()

    @commands.command()
    async def cho(self, ctx: Context):
        """
        `.cho @mention prompt` generate markov chain from prompt.
        Uses server target.
        """
        target = extract_target(ctx)
        prompt = get_command_argument(ctx)
        logger.info(f'{ctx.author.name} requested .cho: target: {target}, prompt: {prompt}')
        prompt = remove_mention(prompt, target)

        response = _continue_prompt(target, prompt)
        if len(response) > 0:
            if isinstance(target, User):
                response = f'{target.name}: {response}'
            await ctx.send(response)
            # await ctx.message.delete()

    @commands.command()
    async def ask(self, ctx: Context):
        """
        `.ask @mention prompt` will try to reply to the prompt's last word.
        Uses the server target.
        """
        target = extract_target(ctx)
        prompt = get_command_argument(ctx)
        logger.info(f'{ctx.author.name} requested .ask: target {target}, prompt: {prompt}')
        prompt = remove_mention(prompt, target)
        await _ask(ctx, target, prompt)

    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        """If someone replies to the bot's message, continue the conversation"""
        if msg.author.id == self.bot.user.id or msg.is_system() \
                or self._message_contains_command(msg):
            return

        # check if it's a reply to this bot
        if msg.reference is not None and \
                msg.reference.resolved.author.id == self.bot.user.id:
            logger.info(f'{msg.author.name} replied to bot: {msg.system_content}')
            await reply_back(msg)
            return
        # check if it's a mention of this bot. It acts like `cho`.
        m = map_message(msg)
        for mention in msg.mentions:
            if mention.id == self.bot.user.id:
                # if mentioned the bot, do 'ask': continue from the last word
                prompt = m.text.replace(f'<@{self.bot.user.id}>', '').strip()
                last_word = get_last_word(prompt)
                logger.info(f'{msg.author.name} mentioned bot: {m.text}')
                response = _continue_prompt(m.server, last_word)
                if len(response) > 0:
                    await msg.channel.send(response)
                    # await msg.delete()

    def _message_contains_command(self, msg: Message) -> bool:
        text: str = msg.system_content or ''
        for command in self.bot.commands:
            if text.find(f'{self.bot.command_prefix}{command.name} ') > -1:
                return True
        return False


def _continue_prompt(target: Target, prompt: str) -> str:
    """Returns empty string if could not continue."""
    model = models_xml.get_model(target)
    if model is None:
        logger.info(f'No model for target {target}')
        return ''
    return _markov_chain_with_retry(model, prompt)


async def reply_back(msg: Message, use_channel: bool = False):
    """
    Reply to the message by continuing the Markov chain from the last word.
    If use_channel == True, will use the channel's model.
    Otherwise, fall back to server model
    """
    m = map_message(msg)
    if m.server is None:
        return  # can't reply outside of server
    last_word = get_last_word(m.text)
    target = m.server
    if use_channel:
        channel_model = models_xml.get_model(m.channel)
        if channel_model is not None:
            target = m.channel
    response = _continue_prompt(target, last_word)
    if len(response) > 0:
        await msg.reply(response)


def _markov_chain_with_retry(model: Model, prompt: str = '') -> str:
    """
    Reruns markov chain multiple times if it fails to do attempts.
    Falls back to running without the prompt, and finally
    falls back to empty string.
    """
    if len(prompt) > 0:
        logger.info(f'Running model "{model.target}" for prompt "{prompt}"...')
    else:
        logger.info(f'Running model "{model.target}" without prompt...')

    attempt_count = 0
    limit = min(config.get('markov_retry_limit', markov_retry_hard_limit), markov_retry_hard_limit)

    while attempt_count < limit:
        chain = markov_chain(model.data, start=prompt)
        if strip_punctuation(chain) != strip_punctuation(prompt):
            logger.info(f'Result: {chain}')
            return chain
        attempt_count += 1
        logger.info(f'Retry {str(attempt_count)}')

    # failed with prompt!

    if len(prompt) > 0:
        # retry without prompt:
        logger.info('Retry without prompt')
        chain = markov_chain(model.data)
        if len(strip_punctuation(chain)) > 0:
            result = f'{prompt} {chain}'
            logger.info(f'Result: {result}')
            return result

    logger.info('No result')
    return ''


async def _ask(ctx: Context, target: Target, prompt: str):
    last_word = get_last_word(prompt)
    model = models_xml.get_model(target)
    if model is None:
        return
    response = _markov_chain_with_retry(model, last_word)
    if len(response) > 0:
        if isinstance(target, User):
            response = f'{target.name}: {response}'
        await ctx.message.reply(response)
