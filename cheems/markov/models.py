import logging
import os
from typing import Dict, Optional

from cheems.config import config
from cheems.markov.model import Model
from cheems.types import Target

logger = logging.getLogger(__name__)

ModelsByTarget = Dict[int, Model]
ModelsByServer = Dict[int, ModelsByTarget]

# models are mapped by server id and then by target id
models_by_server: ModelsByServer = {}
models: list[Model] = []


def load_models():
    """
    Loads all models from the configured directory
    """
    directory = config['markov_model_dir']
    for file in os.listdir(directory):
        full_path = os.path.join(directory, file)
        filename = os.fsdecode(file)
        if filename.endswith('.xml'):
            try:
                with open(full_path) as f:
                    xml_str = f.read()
                m = Model.from_xml(xml_str)
                models.append(m)
                models_by_server.setdefault(m.server_id, {})
                models_by_target = models_by_server[m.server_id]
                models_by_target[m.target_id] = m
            except Exception:
                logger.exception(f'Failed to load model {filename}')
    logger.info(f'Loaded {len(models)} Markov models')


def try_find_model(target: Target) -> Optional[Model]:
    """
    Tries to find the Markov model for this target
    """
    if target.server_id not in models_by_server:
        return None
    models_by_target = models_by_server[target.server_id]
    if target.id not in models_by_target:
        return None
    return models_by_target[target.id]
