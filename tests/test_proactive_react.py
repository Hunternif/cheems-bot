from datetime import datetime, timezone
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, AsyncMock

from cheems.proactive_react_cog import ProactiveReactCog
# test data: Discord objects
from cheems.reaction import reactions
from cheems.targets import Server
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
        system_content='Chinko!', created_at=time, attachments=[],
        add_reaction=AsyncMock()
    )


class TestProactiveReact(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        d_bot_user.configure_mock(id=100, bot=True)
        d_user1.configure_mock(id=123, name='Kagamin', discriminator=1111, bot=False)
        d_channel.configure_mock(id=200, name='Lucky channel', guild=d_server)
        d_server.configure_mock(id=789, name='My server', me=d_bot_user)
        model = reactions.create_model(Server(789, 'My server'))
        model.data = {'reaction': 1}

    async def test_reply_after_period(self):
        override_test_config('''
proactive_react:
  period_msgs: 3
  servers:
    My server:
      channels:
        allowlist:
          - Lucky channel
        ''')
        cog = ProactiveReactCog(Mock(user=d_bot))

        msg = _make_msg()
        await cog.on_message(msg)
        msg.add_reaction.assert_not_called()

        msg = _make_msg()
        await cog.on_message(msg)
        msg.add_reaction.assert_not_called()

        msg = _make_msg()
        await cog.on_message(msg)
        msg.add_reaction.assert_called_with('reaction')

        msg = _make_msg()
        await cog.on_message(msg)
        msg.add_reaction.assert_not_called()

    async def test_reply_no_period(self):
        override_test_config('''
proactive_react:
  period_msgs: 0
  servers:
    My server:
      channels:
        allowlist:
          - Lucky channel
        ''')
        cog = ProactiveReactCog(Mock(user=d_bot))

        msg = _make_msg()
        await cog.on_message(msg)
        msg.add_reaction.assert_called_with('reaction')

        msg = _make_msg()
        await cog.on_message(msg)
        msg.add_reaction.assert_called_with('reaction')

    async def test_reply_blocked_server(self):
        override_test_config('''
proactive_react:
  period_msgs: 0
  servers:
    Other server:
        ''')
        cog = ProactiveReactCog(Mock(user=d_bot))

        msg = _make_msg()
        await cog.on_message(msg)
        msg.add_reaction.assert_not_called()

    async def test_reply_blocked_channel(self):
        override_test_config('''
proactive_react:
  period_msgs: 0
  servers:
    My server:
      channels:
        allowlist:
          -
        ''')
        cog = ProactiveReactCog(Mock(user=d_bot))

        msg = _make_msg()
        await cog.on_message(msg)
        msg.add_reaction.assert_not_called()
