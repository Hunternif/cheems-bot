from datetime import datetime
from importlib import reload
from unittest import TestCase
from unittest.mock import Mock, MagicMock

from discord.ext.commands import Context

from cheems.discord_helper import extract_target, map_message
from cheems.markov import models_xml
from cheems.targets import User, Server, Channel, Message

# test data: Discord objects
d_user1 = Mock()
d_user2 = Mock()
d_bot = Mock()
d_channel = Mock()
d_dm_channel = MagicMock()
d_server = Mock()
time = datetime.now()

# test data: my domain objects
server = Server(789, 'My server')
channel = Channel(200, 'Lucky channel', server)
user1 = User(123, 'Kagamin', 1111, server)
user2 = User(456, 'Tsukasa', 2222, server)


class TestDiscordHelper(TestCase):
    @classmethod
    def setUpClass(cls):
        d_user1.configure_mock(id=123, name='Kagamin', discriminator=1111, bot=False)
        d_user2.configure_mock(id=456, name='Tsukasa', discriminator=2222, bot=False)
        d_bot.configure_mock(id=100, bot=True)
        d_channel.configure_mock(id=200, name='Lucky channel', guild=d_server)
        d_dm_channel.configure_mock(id=201)
        del d_dm_channel.guild
        del d_dm_channel.created_at
        d_dm_channel.__str__ = Mock(return_value='Direct channel name')
        d_server.configure_mock(id=789, name='My server', me=d_bot)

    def setUp(self) -> None:
        # Reload models_xml.py because the directory in the config changed,
        # and to clean old references to saved models
        reload(models_xml)

    def test_extract_target_first_user(self):
        msg = Mock(mentions=[d_user1, d_user2], guild=d_server)
        ctx = Context(prefix='.', message=msg)
        target = extract_target(ctx)
        self.assertEqual(user1, target)

    def test_extract_target_ignore_bot(self):
        msg = Mock(mentions=[d_bot, d_user2], guild=d_server)
        ctx = Context(prefix='.', message=msg)
        target = extract_target(ctx)
        self.assertEqual(user2, target)

    def test_extract_target_channel(self):
        msg = Mock(mentions=[], channel_mentions=[d_channel], guild=d_server, system_content='')
        ctx = Context(prefix='.', message=msg)
        target = extract_target(ctx)
        self.assertEqual(channel, target)

    def test_extract_target_server(self):
        msg = Mock(mentions=[], channel_mentions=[], guild=d_server, system_content='')
        ctx = Context(prefix='.', message=msg)
        target = extract_target(ctx)
        self.assertEqual(server, target)

    def test_map_message(self):
        d_msg = Mock(
            guild=d_server, author=d_user1, channel=d_channel, system_content='Chinko!', created_at=time,
            attachments=[]
        )
        msg = map_message(d_msg)
        self.assertEqual(Message(
            user=user1,
            channel=channel,
            server=server,
            text='Chinko!',
            created_at=time,
        ), msg)

    def test_map_direct_message(self):
        d_msg = MagicMock(
            author=d_user1, channel=d_dm_channel, system_content='Chinko!', created_at=time,
            attachments=[]
        )
        del d_msg.guild
        msg = map_message(d_msg)
        self.assertEqual(Message(
            user=User(123, 'Kagamin', 1111, None),
            channel=Channel(201, 'Direct channel name', None),
            server=None,
            text='Chinko!',
            created_at=time,
        ), msg)

    def test_map_invalid_message(self):
        d_msg = Mock(
            guild=d_server, author=d_user1, channel=d_channel, system_content=None, created_at=time,
            attachments=[]
        )
        msg = map_message(d_msg)
        self.assertEqual(Message(
            user=user1,
            channel=channel,
            server=server,
            text='',
            created_at=time,
        ), msg)

    def test_extract_mention(self):
        models_xml.create_model(user1)
        msg = Mock(mentions=[d_user1], channel_mentions=[], guild=d_server, system_content='.che привет')
        ctx = Context(prefix='.', message=msg)
        self.assertEqual(user1, extract_target(ctx))

    # def test_extract_mention_from_simple_name(self):
    #     models_xml.create_model(user1)
    #     msg = Mock(mentions=[], channel_mentions=[], guild=d_server, system_content='.che kagamin')
    #     ctx = Context(prefix='.', message=msg)
    #     self.assertEqual(user1, extract_target(ctx))
    #
    # def test_extract_mention_from_simple_name_with_extra_words(self):
    #     models_xml.create_model(user1)
    #     msg = Mock(mentions=[], channel_mentions=[], guild=d_server, system_content='.cho kagamin хаха')
    #     ctx = Context(prefix='.', message=msg)
    #     self.assertEqual(user1, extract_target(ctx))

    def test_extract_mention_only_in_2nd_position(self):
        models_xml.create_model(user1)
        msg = Mock(mentions=[], channel_mentions=[], guild=d_server, system_content='kagamin хаха')
        ctx = Context(prefix='.', message=msg)
        self.assertEqual(server, extract_target(ctx))
