import logging
import sys

import yaml

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


config = {}

try:
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
except Exception:
    logger.exception("Couldn't read config.yaml")
