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

try:
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
except Exception:
    logger.exception("Couldn't read config.yaml")
