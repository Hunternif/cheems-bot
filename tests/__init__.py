import yaml

import cheems.config

# load test config
with open('tests/test_config.yaml', 'r', encoding='utf-8') as f:
    cheems.config.config = yaml.safe_load(f)
