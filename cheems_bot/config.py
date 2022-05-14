import logging
import sys

import yaml

# Config variables
discord_token = ''


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

try:
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
        discord_token = config['discord_token']
except Exception:
    logger.exception("Couldn't read config.yaml")
