from unittest import TestCase
from unittest.mock import Mock

from discord.ext.commands import Context

from cheems.discord_helper import extract_target, map_message
from cheems.types import User, Server, Channel, Message

# test data
user1 = Mock()
user2 = Mock()
bot = Mock()
channel = Mock()
server = Mock()


class TestDiscordHelper(TestCase):
    @classmethod
    def setUpClass(cls):
        user1.configure_mock(id=123, name='Kagamin', discriminator=1111)
        user2.configure_mock(id=456, name='Tsukasa', discriminator=2222)
        bot.configure_mock(id=100)
        channel.configure_mock(id=200, name='Lucky channel')
        server.configure_mock(id=789, name='My server', me=bot)

    def test_extract_target_first_user(self):
        msg = Mock(mentions=[user1, user2], guild=server)
        ctx = Context(prefix='.', message=msg)
        target = extract_target(ctx)
        self.assertEqual(User(123, 'Kagamin', 1111, Server(789, 'My server')), target)

    def test_extract_target_ignore_bot(self):
        msg = Mock(mentions=[bot, user2], guild=server)
        ctx = Context(prefix='.', message=msg)
        target = extract_target(ctx)
        self.assertEqual(User(456, 'Tsukasa', 2222, Server(789, 'My server')), target)

    def test_extract_target_channel(self):
        msg = Mock(mentions=[], channel_mentions=[channel], guild=server)
        ctx = Context(prefix='.', message=msg)
        target = extract_target(ctx)
        self.assertEqual(Channel(200, 'Lucky channel', Server(789, 'My server')), target)

    def test_extract_target_server(self):
        msg = Mock(mentions=[], channel_mentions=[], guild=server)
        ctx = Context(prefix='.', message=msg)
        target = extract_target(ctx)
        self.assertEqual(Server(789, 'My server'), target)

    def test_map_message(self):
        d_msg = Mock(guild=server, author=user1, channel=channel, clean_content='Chinko!')
        msg = map_message(d_msg)
        self.assertEqual(Message(
            user=User(123, 'Kagamin', 1111, Server(789, 'My server')),
            channel=Channel(200, 'Lucky channel', Server(789, 'My server')),
            server=Server(789, 'My server'),
            text='Chinko!',
        ), msg)
