# load test config
import yaml

from cheems.config import load_config, config

load_config('tests/test_config.yaml')


def override_test_config(yaml_content: str):
    """Should only be called from tests"""
    new_dict = yaml.safe_load(yaml_content)
    config.read_dict(new_dict)
