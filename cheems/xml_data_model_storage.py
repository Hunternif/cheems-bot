import logging
import os
from datetime import datetime, timezone
from typing import Dict, Optional

from cheems.base_xml_data_model import BaseXmlDataModel
from cheems.discord_helper import EPOCH
from cheems.targets import Target, Server, Channel, User
from cheems.util import sanitize_filename

logger = logging.getLogger(__name__)


class XmlDataModelStorage:
    """
    Loads and saves instances of BaseXmlDataModel classes in a directory.
    """
    root_dir: str

    ModelsByTarget = Dict[Target, BaseXmlDataModel]
    ModelsByServer = Dict[int, ModelsByTarget]

    # models are mapped by server id and then by target id
    models_by_server_id: ModelsByServer
    models: list[BaseXmlDataModel]

    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.models_by_server_id = {}
        self.models = []

    def _register_model(self, m: BaseXmlDataModel):
        self.models.append(m)
        self.models_by_server_id.setdefault(m.server_id, {})
        models_by_target = self.models_by_server_id[m.server_id]
        models_by_target[m.target] = m

    def load_models(self):
        """
        Loads all models from the configured directory
        """
        subdir: str
        files: list[str]
        for subdir, _, files in os.walk(self.root_dir):
            for file in files:
                full_path: str = os.path.join(subdir, file)
                filename = os.fsdecode(file)
                if filename.endswith('.xml'):
                    try:
                        m = BaseXmlDataModel.from_xml_file(full_path)
                        self._register_model(m)
                    except Exception:
                        logger.exception(f'Failed to load model {filename}')
        logger.info(f'Loaded {len(self.models)} XMl models')

    def save_model(self, xml_model: BaseXmlDataModel):
        """
        Saves model into the xml file, as written in attr 'file_path'
        """
        if xml_model.file_path is None:
            # this shouldn't happen, so we'll save it in a special folder 'lost'
            dir_name = f'{xml_model.server_id}'
            subdir = os.path.join(self.root_dir, 'lost', dir_name)
            if not os.path.exists(subdir):
                os.makedirs(subdir)
            filename = f'{str(datetime.now())}.xml'
            file_path = os.path.join(subdir, filename)
            xml_model.file_path = file_path
        with open(xml_model.file_path, 'w', encoding='utf-8') as f:
            f.write(xml_model.to_xml())

    def create_model(self, target: Target) -> BaseXmlDataModel:
        """
        Creates model file and return the new model
        """
        xml_model = BaseXmlDataModel(
            from_time=EPOCH,
            to_time=EPOCH,
            updated_time=datetime.now(tz=timezone.utc),
            target=target,
            description=str(target),
            raw_data='',
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
        subdir: str = os.path.join(self.root_dir, server_dir, target_dir)
        if not os.path.exists(subdir):
            os.makedirs(subdir)
        filename = f'{target.id} {sanitize_filename(target.name)}.xml'
        file_path: str = os.path.join(subdir, filename)
        xml_model.file_path = file_path

        self._register_model(xml_model)
        logger.info(f'Created model {file_path}')
        return xml_model

    def get_or_create_model(self, target: Target) -> BaseXmlDataModel:
        """
        Finds an existing model for this target, or creates a new one.
        """
        model = self.get_model(target)
        if model is None:
            model = self.create_model(target)
        return model

    def get_model(self, target: Target) -> Optional[BaseXmlDataModel]:
        """
        Finds an existing model for this target, does not create new model.
        """
        if target.server_id not in self.models_by_server_id:
            return None
        models_by_target = self.models_by_server_id[target.server_id]
        if target not in models_by_target:
            return None
        return models_by_target[target]
