from datetime import datetime, timezone, timedelta
from importlib import reload
from tempfile import TemporaryDirectory
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock

from cheems.config import config
from cheems.discord_helper import map_channel
from cheems.markov import models_xml
from cheems.trainer import CheemsTrainer

# test data: Discord objects
from tests import override_test_config

d_bot_user = Mock()
d_bot = Mock()
d_user1 = Mock()
d_bad_user = Mock()

d_my_server = Mock()
d_lucky_channel = Mock()

d_my_other_server = Mock()
d_general_channel = Mock()

d_banned_server = Mock()
d_banned_channel = Mock()

d_other_server_2 = Mock()
d_other_channel_2 = Mock()

today = datetime.now(tz=timezone.utc)
yesterday = today - timedelta(days=1)


def _make_msg(author: any = d_user1, channel: any = d_lucky_channel,
              content: str = 'hello world', time: datetime = yesterday):
    return Mock(
        guild=d_lucky_channel.guild, author=author, channel=channel,
        system_content=content, created_at=time, attachments=[]
    )


class TestTraining(IsolatedAsyncioTestCase):
    temp_dir: TemporaryDirectory

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = TemporaryDirectory()
        override_test_config(f'markov_moodel_dir: {cls.temp_dir.name}')

        d_bot_user.configure_mock(id=100, bot=True)
        d_bot.configure_mock(user=d_bot_user, guilds=[
            d_my_server, d_my_other_server, d_banned_server, d_other_server_2
        ])
        d_user1.configure_mock(id=123, name='Kagamin', discriminator=1111, bot=False)
        d_bad_user.configure_mock(id=124, name='Konata', discriminator=1112, bot=False)

        d_my_server.configure_mock(id=789, name='My server', text_channels=[d_lucky_channel], me=d_bot_user)
        d_my_other_server.configure_mock(id=790, name='My other server', text_channels=[d_general_channel], me=d_bot_user)
        d_banned_server.configure_mock(id=791, name='Banned server', text_channels=[d_banned_channel], me=d_bot_user)
        d_other_server_2.configure_mock(id=792, name='Other server', text_channels=[d_other_channel_2], me=d_bot_user)

        d_lucky_channel.configure_mock(id=200, name='lucky_channel', guild=d_my_server)
        d_general_channel.configure_mock(id=201, name='general', guild=d_my_other_server)
        d_banned_channel.configure_mock(id=202, name='general', guild=d_banned_server)
        d_other_channel_2.configure_mock(id=203, name='general', guild=d_other_server_2)

        override_test_config('''
training:
  message_limit: 100
  wait_sec: 0
  servers:
    My server:
      channels:
        blocklist:
          - bot_testing
          - bot_testing2
        nsfw:
          - nsfw_channel
        special:
          - deer-gacha
      users:
        special:
          - my_bot
      bad_msg:
        - 1024851143001641020
    My other server:
      channels:
        allowlist:
          - general
      users:
        blocklist:
          - BadGuy
    Banned server:
      channels:
        allowlist:
          -
        ''')

    def setUp(self) -> None:
        # Reload models_xml.py because the directory in the config changed,
        # and to clean old references to saved models
        reload(models_xml)
        reset_channels()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()

    async def test_basic_training(self):
        self.assertEqual(100, int(config['training']['message_limit']))
        self.assertEqual(0, int(config['training']['wait_sec']))

        set_messages([
            _make_msg(content='hello world'),
            _make_msg(content='hello world'),
            _make_msg(content='hello baby'),
        ])

        trainer = CheemsTrainer(d_bot)
        trainer.begin_training()
        await trainer.wait_for_completion()

        self.assertEqual('''
baby . 1
hello baby 1
hello world 2
world . 2
        '''.strip(), get_model_data(d_lucky_channel))
        self.assertIsNone(models_xml.get_model(d_general_channel))

    async def test_training_multiple_servers(self):
        set_messages([
            _make_msg(content='hello world', channel=d_lucky_channel),
            _make_msg(content='hello general', channel=d_general_channel),
            _make_msg(content='hello baby', channel=d_lucky_channel),
        ])

        trainer = CheemsTrainer(d_bot)
        await trainer.update_models_from_channel(d_lucky_channel, yesterday)
        await trainer.update_models_from_channel(d_general_channel, yesterday)

        self.assertEqual('''
baby . 1
hello baby 1
hello world 1
world . 1
        '''.strip(), get_model_data(d_lucky_channel))
        self.assertEqual('''
general . 1
hello general 1
        '''.strip(), get_model_data(d_general_channel))

    async def test_banned_server(self):
        set_messages([
            _make_msg(content='hello world', channel=d_banned_channel),
        ])

        trainer = CheemsTrainer(d_bot)
        await trainer.update_models_from_channel(d_banned_channel, yesterday)

        self.assertIsNone(models_xml.get_model(d_banned_channel))

    async def test_unlisted_server(self):
        set_messages([
            _make_msg(content='hello world', channel=d_other_channel_2),
        ])

        trainer = CheemsTrainer(d_bot)
        await trainer.update_models_from_channel(d_other_channel_2, yesterday)

        self.assertIsNone(models_xml.get_model(d_other_channel_2))


def set_messages(msgs: list[any]):
    """Queues up the messages so that they can be read from their channel's history"""
    channels = {}
    for msg in msgs:
        channel_history = channels.get(msg.channel, [])
        channel_history.append(msg)
        channels[msg.channel] = channel_history

    def create_history_function(msg_list: list[any]):
        async def get_history(limit, after, oldest_first):
            for m in msg_list:
                yield m
            msg_list.clear()  # return no more messages after this
        return get_history

    for channel, msg_list in channels.items():
        channel.configure_mock(history=create_history_function(msg_list))


def reset_channels():
    async def empty_history(limit, after, oldest_first):
        return
        yield  # 'yield' makes it an async generator
    for ch in [d_lucky_channel, d_general_channel, d_banned_channel, d_other_channel_2]:
        ch.configure_mock(history=empty_history)


def get_model_data(channel: any) -> str:
    model = models_xml.get_model(map_channel(channel))
    return model.serialize_data()
