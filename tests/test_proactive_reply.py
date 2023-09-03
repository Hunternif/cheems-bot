from datetime import datetime, timezone
from unittest import mock, IsolatedAsyncioTestCase
from unittest.mock import Mock, AsyncMock

from cheems.markov_cog import reply_back
from cheems.proactive_markov_cog import ProactiveMarkovCog

# test data: Discord objects
from tests import override_test_config

d_bot = Mock()
d_user1 = Mock()
d_bot_user = Mock()
d_channel = Mock()
d_server = Mock()


def _make_msg(author: any = d_user1, channel: any = d_channel):
    time = datetime.now(tz=timezone.utc)
    return Mock(
        guild=d_server, author=author, channel=channel,
        system_content='Chinko!', created_at=time, attachments=[]
    )


class TestProactiveReply(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        d_bot_user.configure_mock(id=100, bot=True)
        d_user1.configure_mock(id=123, name='Kagamin', discriminator=1111, bot=False)
        d_channel.configure_mock(id=200, name='Lucky channel', guild=d_server)
        d_server.configure_mock(id=789, name='My server', me=d_bot_user)

    @mock.patch('cheems.proactive_markov_cog.reply_back')
    async def test_reply_after_period(self, reply_mock_fn: AsyncMock) -> None:
        override_test_config('''
proactive_reply:
  period_msgs: 3
  servers:
    My server:
      channels:
        allowlist:
          - Lucky channel
        ''')
        cog = ProactiveMarkovCog(Mock(user=d_bot))

        await cog.on_message(_make_msg())
        reply_mock_fn.assert_not_called()

        await cog.on_message(_make_msg())
        reply_mock_fn.assert_not_called()

        msg = _make_msg()
        await cog.on_message(msg)
        reply_mock_fn.assert_called_with(msg, use_channel=True)

        reply_mock_fn.reset_mock()
        await cog.on_message(_make_msg())
        reply_mock_fn.assert_not_called()

    @mock.patch('cheems.proactive_markov_cog.reply_back')
    async def test_reply_no_period(self, reply_mock_fn: AsyncMock) -> None:
        override_test_config('''
proactive_reply:
  period_msgs: 0
  servers:
    My server:
      channels:
        allowlist:
          - Lucky channel
        ''')
        cog = ProactiveMarkovCog(Mock(user=d_bot))

        msg = _make_msg()
        await cog.on_message(msg)
        await reply_back(msg)
        reply_mock_fn.assert_called_with(msg, use_channel=True)

        reply_mock_fn.reset_mock()
        await cog.on_message(msg)
        await reply_back(msg)
        reply_mock_fn.assert_called_with(msg, use_channel=True)

    @mock.patch('cheems.proactive_markov_cog.reply_back')
    async def test_reply_blocked_server(self, reply_mock_fn: AsyncMock) -> None:
        override_test_config('''
proactive_reply:
  period_msgs: 0
  servers:
    Other server:
        ''')
        cog = ProactiveMarkovCog(Mock(user=d_bot))

        await cog.on_message(_make_msg())
        reply_mock_fn.assert_not_called()

    @mock.patch('cheems.proactive_markov_cog.reply_back')
    async def test_reply_blocked_channel(self, reply_mock_fn: AsyncMock) -> None:
        override_test_config('''
proactive_reply:
  period_msgs: 0
  servers:
    My server:
      channels:
        allowlist:
          -
        ''')
        cog = ProactiveMarkovCog(Mock(user=d_bot))

        await cog.on_message(_make_msg())
        reply_mock_fn.assert_not_called()
