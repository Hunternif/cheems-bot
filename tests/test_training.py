from datetime import datetime, timezone, timedelta
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock

import yaml

from cheems.config import config
from cheems.discord_helper import map_channel
from cheems.markov import models_xml
from cheems.trainer import CheemsTrainer

# test data: Discord objects
d_bot = Mock()
d_user1 = Mock()
d_bot_user = Mock()
d_channel = Mock()
d_server = Mock()


def _make_msg(author: any = d_user1, channel: any = d_channel,
              content: str = 'hello world', time: datetime = None):
    if not time:
        time = datetime.now(tz=timezone.utc)
    return Mock(
        guild=d_server, author=author, channel=channel,
        system_content=content, created_at=time, attachments=[]
    )


class TestTraining(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        d_bot_user.configure_mock(id=100, bot=True)
        d_user1.configure_mock(id=123, name='Kagamin', discriminator=1111, bot=False)
        d_channel.configure_mock(id=200, name='lucky_channel', guild=d_server)
        d_server.configure_mock(id=789, name='My server', me=d_bot_user)

    async def test_training_allowlist(self):
        config['training'] = yaml.load('''
message_limit: 100
wait_sec: 1
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
        ''', yaml.BaseLoader)
        self.assertEqual(100, int(config['training']['message_limit']))
        self.assertEqual(1, int(config['training']['wait_sec']))

        msg = _make_msg(content='hello world')

        async def get_history(limit, after, oldest_first):
            yield msg

        d_channel.configure_mock(history=get_history)
        time = datetime.now(tz=timezone.utc) - timedelta(days=1)

        trainer = CheemsTrainer(Mock(user=d_bot))
        await trainer.update_models_from_channel(d_channel, time)

        ch = map_channel(d_channel)
        model = models_xml.get_or_create_model(ch)
        model_data = model.serialize_data()
        self.assertEqual('hello world 1\nworld . 1', model_data)
