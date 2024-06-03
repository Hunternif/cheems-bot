import logging
import sys

import yaml

from cheems.targets import Target, Server, Channel, User, Message

# Logger config
root = logging.getLogger()
root.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

# Local logger
logger = logging.getLogger(__name__)


def is_name_allowed(config: dict, name: str) -> bool:
    """
    Assuming the config contains an allowlist and/or a blocklist,
    returns true if this name is allowed.
    """
    allowlist = config.get('allowlist', None)
    blocklist = config.get('blocklist', [])
    if isinstance(allowlist, list) and name not in allowlist:
        return False
    if isinstance(blocklist, list) and name in blocklist:
        return False
    return True


def is_name_special(config: dict, name: str) -> bool:
    """
    Certain channels or users can be considered too spammy to contibute
    to the main dataset, but they may be interesting on their own.
    Messages from these channels will only update their own config.
    """
    special_list = config.get('special', [])
    if name in special_list:
        return True
    return False


def is_message_id_allowed(config: dict, id: int) -> bool:
    """
    Certain specific messages can be blocked per server config.
    """
    bad_msg = config.get('bad_msg', [])
    if id in bad_msg:
        return False
    return True


def is_channel_sfw(server_name: str, channel_name: str) -> bool:
    server_config = config.get('training', {}).get('servers', {}).get(server_name, {})
    channel_config = server_config.get('channels', {})
    nsfw = channel_config.get('nsfw', [])
    if isinstance(nsfw, list) and channel_name in nsfw:
        return False
    return True


class CheemsConfig:
    """
    The default implementation uses the YAML config file.
    """
    inner_dict: dict = {}

    def read_dict(self, new_dict: dict):
        self.inner_dict.update(new_dict)

    def is_feature_allowed(self, feature: str, target: Target = None) -> bool:
        """Returns true if the feature is allowed in this target"""
        if target is None:
            # no target given, just check that the feature name is present:
            return feature in self.inner_dict

        try:
            feature_config = self.inner_dict.get(feature)
            servers = feature_config.get('servers', {})

            if isinstance(target, Server):
                return target.name in servers

            if isinstance(target, Channel):
                server_config = servers.get(target.server.name)
                channel_config = server_config.get('channels', {})
                return is_name_allowed(channel_config, target.name)

            if isinstance(target, User):
                server_config = servers.get(target.server.name)
                user_config = server_config.get('users', {})
                return is_name_allowed(user_config, target.name)

            if isinstance(target, Message):
                server_config = servers.get(target.server.name)
                channel_config = server_config.get('channels', {})
                user_config = server_config.get('users', {})
                # TODO: check if message id is in 'bad_msg'?
                return is_name_allowed(channel_config, target.channel.name) and \
                       is_name_allowed(user_config, target.user.name)
        except Exception:
            return False

    def get(self, key: str, default: any = None, target: Target = None) -> any:
        """Returns the value for key, given the current target"""
        return self.inner_dict[key]

    def __getitem__(self, item) -> any:
        return self.get(item)


config: CheemsConfig = CheemsConfig()
"""
This config is imported in many modules, and is meant to be read-only.
Might be an anti-pattern.
"""


def load_config(path: str):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f)
            config.read_dict(yaml_content)
    except Exception as e:
        logger.exception("Couldn't read config.yaml")
        raise e


# Auto-load config, because other modules importing 'config' depend on it being loaded
load_config('config.yaml')
