import logging
import os
from datetime import datetime
from typing import Dict

from cheems.config import config
from cheems.markov.model import Model
from cheems.types import Target, Server, Channel, User
from cheems.util import sanitize_filename

logger = logging.getLogger(__name__)
root_dir = config['markov_model_dir']

ModelsByTarget = Dict[int, Model]
ModelsByServer = Dict[int, ModelsByTarget]

# models are mapped by server id and then by target id
models_by_server: ModelsByServer = {}
models: list[Model] = []


def _register_model(m: Model):
    models.append(m)
    models_by_server.setdefault(m.server_id, {})
    models_by_target = models_by_server[m.server_id]
    models_by_target[m.target_id] = m


def load_model_from_xml(file_path) -> Model:
    """
    After a model is loaded, the path to its file will be stored in attr 'file_path'
    """
    with open(file_path, encoding='utf-8') as f:
        xml_str = f.read()
    m = Model.from_xml(xml_str)
    m.file_path = file_path
    _register_model(m)
    return m


def load_models():
    """
    Loads all models from the configured directory
    """
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            full_path = os.path.join(subdir, file)
            filename = os.fsdecode(file)
            if filename.endswith('.xml'):
                try:
                    load_model_from_xml(full_path)
                except Exception:
                    logger.exception(f'Failed to load model {filename}')
    logger.info(f'Loaded {len(models)} Markov models')


def save_model(model: Model):
    """
    Saves model into the xml file, as written in attr 'file_path'
    """
    if not hasattr(model, 'file_path'):
        # this shouldn't happen, so we'll save it in a special folder 'lost'
        dir_name = f'{model.server_id}'
        subdir = os.path.join(root_dir, 'lost', dir_name)
        if not os.path.exists(subdir):
            os.mkdir(subdir)
        filename = f'{model.target_id}.xml'
        file_path = os.path.join(subdir, filename)
        model.file_path = file_path
    with open(model.file_path, 'w', encoding='utf-8') as f:
        f.write(model.to_xml())


def create_model(target: Target) -> Model:
    """
    Creates model file and return the new model
    """
    model = Model(
        from_time=target.created_at,
        to_time=target.created_at,
        updated_time=datetime.now(),
        server_id=target.server_id,
        target_id=target.id,
        description=str(target)
    )
    if hasattr(target, 'server'):
        server: Server = target.server
        server_dir = f'{server.id} {sanitize_filename(server.name)}'
    else:
        server_dir = f'{target.server_id}'
    if isinstance(target, Channel):
        target_dir = 'channels'
    elif isinstance(target, User):
        target_dir = 'users'
    else:
        target_dir = ''
    subdir = os.path.join(root_dir, server_dir, target_dir)
    if not os.path.exists(subdir):
        os.makedirs(subdir)
    filename = f'{target.id} {sanitize_filename(target.name)}.xml'
    file_path = os.path.join(subdir, filename)
    model.file_path = file_path
    save_model(model)
    _register_model(model)
    logger.info(f'Created model {file_path}')
    return model


def get_or_create_model(target: Target) -> Model:
    """
    Finds an existing Markov model for this target, or creates a new one.
    """
    if target.server_id not in models_by_server:
        return create_model(target)
    models_by_target = models_by_server[target.server_id]
    if target.id not in models_by_target:
        return create_model(target)
    return models_by_target[target.id]
