import logging
import os
from datetime import datetime
from typing import Dict, Optional

from cheems.config import config
from cheems.markov.model import Model
from cheems.markov.model_xml import XmlModel
from cheems.types import Target, Server, Channel, User
from cheems.util import sanitize_filename

logger = logging.getLogger(__name__)
root_dir: str = config['markov_model_dir']

ModelsByTarget = Dict[int, XmlModel]
ModelsByServer = Dict[int, ModelsByTarget]

# models are mapped by server id and then by target id
models_by_server: ModelsByServer = {}
models: list[XmlModel] = []


def _register_model(m: XmlModel):
    models.append(m)
    models_by_server.setdefault(m.model.server_id, {})
    models_by_target = models_by_server[m.model.server_id]
    models_by_target[m.model.target_id] = m


def load_models():
    """
    Loads all models from the configured directory
    """
    subdir: str
    files: list[str]
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            full_path: str = os.path.join(subdir, file)
            filename = os.fsdecode(file)
            if filename.endswith('.xml'):
                try:
                    m = XmlModel.from_xml_file(full_path)
                    _register_model(m)
                except Exception:
                    logger.exception(f'Failed to load model {filename}')
    logger.info(f'Loaded {len(models)} Markov models')


def save_model(xml_model: XmlModel):
    """
    Saves model into the xml file, as written in attr 'file_path'
    """
    model = xml_model.model
    if xml_model.file_path is None:
        # this shouldn't happen, so we'll save it in a special folder 'lost'
        dir_name = f'{model.server_id}'
        subdir = os.path.join(root_dir, 'lost', dir_name)
        if not os.path.exists(subdir):
            os.mkdir(subdir)
        filename = f'{model.target_id}.xml'
        file_path = os.path.join(subdir, filename)
        xml_model.file_path = file_path
    with open(xml_model.file_path, 'w', encoding='utf-8') as f:
        f.write(xml_model.to_xml())


def create_model(target: Target) -> XmlModel:
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
    if isinstance(target, Server):
        server_dir = f'{target.id} {sanitize_filename(target.name)}'
    elif hasattr(target, 'server'):
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
    subdir: str = os.path.join(root_dir, server_dir, target_dir)
    if not os.path.exists(subdir):
        os.makedirs(subdir)
    filename = f'{target.id} {sanitize_filename(target.name)}.xml'
    file_path: str = os.path.join(subdir, filename)

    xml_model = XmlModel(model, file_path)
    save_model(xml_model)
    _register_model(xml_model)
    logger.info(f'Created model {file_path}')
    return xml_model


def get_or_create_model(target: Target) -> XmlModel:
    """
    Finds an existing Markov model for this target, or creates a new one.
    """
    if target.server_id not in models_by_server:
        return create_model(target)
    models_by_target = models_by_server[target.server_id]
    if target.id not in models_by_target:
        return create_model(target)
    return models_by_target[target.id]


def get_model(target: Target) -> Optional[XmlModel]:
    """
    Finds an existing Markov model for this target, does not create new model.
    """
    if target.server_id not in models_by_server:
        return None
    models_by_target = models_by_server[target.server_id]
    if target.id not in models_by_target:
        return None
    return models_by_target[target.id]
