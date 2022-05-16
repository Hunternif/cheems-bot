from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock, MagicMock

from discord.ext.commands import Context

from cheems.discord_helper import extract_target, map_message
from cheems.types import User, Server, Channel, Message

# test data
user1 = Mock()
user2 = Mock()
bot = Mock()
channel = Mock()
dm_channel = MagicMock()
server = Mock()
time = datetime.now()


class TestDiscordHelper(TestCase):
    @classmethod
    def setUpClass(cls):
        user1.configure_mock(id=123, name='Kagamin', discriminator=1111, created_at=time)
        user2.configure_mock(id=456, name='Tsukasa', discriminator=2222, created_at=time)
        bot.configure_mock(id=100, created_at=time)
        channel.configure_mock(id=200, name='Lucky channel', guild=server, created_at=time)
        dm_channel.configure_mock(id=201)
        del dm_channel.guild
        del dm_channel.created_at
        dm_channel.__str__ = Mock(return_value='Direct channel name')
        server.configure_mock(id=789, name='My server', me=bot, created_at=time)

    def test_extract_target_first_user(self):
        msg = Mock(mentions=[user1, user2], guild=server, created_at=time)
        ctx = Context(prefix='.', message=msg)
        target = extract_target(ctx)
        self.assertEqual(User(123, 'Kagamin', time, 1111, Server(789, 'My server', time)), target)

    def test_extract_target_ignore_bot(self):
        msg = Mock(mentions=[bot, user2], guild=server, created_at=time)
        ctx = Context(prefix='.', message=msg)
        target = extract_target(ctx)
        self.assertEqual(User(456, 'Tsukasa', time, 2222, Server(789, 'My server', time)), target)

    def test_extract_target_channel(self):
        msg = Mock(mentions=[], channel_mentions=[channel], guild=server, created_at=time)
        ctx = Context(prefix='.', message=msg)
        target = extract_target(ctx)
        self.assertEqual(Channel(200, 'Lucky channel', time, Server(789, 'My server', time)), target)

    def test_extract_target_server(self):
        msg = Mock(mentions=[], channel_mentions=[], guild=server, created_at=time)
        ctx = Context(prefix='.', message=msg)
        target = extract_target(ctx)
        self.assertEqual(Server(789, 'My server', time), target)

    def test_map_message(self):
        d_msg = Mock(guild=server, author=user1, channel=channel, clean_content='Chinko!', created_at=time)
        msg = map_message(d_msg)
        self.assertEqual(Message(
            user=User(123, 'Kagamin', time, 1111, Server(789, 'My server', time)),
            channel=Channel(200, 'Lucky channel', time, Server(789, 'My server', time)),
            server=Server(789, 'My server', time),
            text='Chinko!',
            created_at=time,
        ), msg)

    def test_map_direct_message(self):
        d_msg = MagicMock(author=user1, channel=dm_channel, clean_content='Chinko!', created_at=time)
        del d_msg.guild
        msg = map_message(d_msg)
        self.assertEqual(Message(
            user=User(123, 'Kagamin', time, 1111, None),
            channel=Channel(201, 'Direct channel name', datetime.utcfromtimestamp(0), None),
            server=None,
            text='Chinko!',
            created_at=time,
        ), msg)
