import logging
from typing import Dict, Optional

from cheems.config import config
from cheems.markov.model import Model
from cheems.markov.model_xml import XmlModel
from cheems.targets import Target
from cheems.xml_data_model_storage import XmlDataModelStorage

logger = logging.getLogger(__name__)

ModelsByTarget = Dict[Target, XmlModel]
ModelsByServer = Dict[int, ModelsByTarget]


class MarkovStorage:
    # Having duplicate raw strings inside XmlDataModelStorage and
    # parsed XmlModel might be a waste of memory...
    xml_storage: XmlDataModelStorage

    # models are mapped by server id and then by target id
    models_by_server_id: ModelsByServer
    models: list[XmlModel]

    def __init__(self):
        self.xml_storage = XmlDataModelStorage(config['markov_model_dir'])
        self.models_by_server_id = {}
        self.models = []

    def _register_model(self, m: XmlModel):
        self.models.append(m)
        self.models_by_server_id.setdefault(m.server_id, {})
        models_by_target = self.models_by_server_id[m.server_id]
        models_by_target[m.target] = m

    def load_models(self):
        self.xml_storage.load_models()
        for xml_model in self.xml_storage.models:
            model = XmlModel.from_base_model(xml_model)
            self._register_model(model)

    def save_model(self, model: Model):
        xml_model = model if isinstance(model, XmlModel) else XmlModel.from_model(model)
        self.xml_storage.save_model(xml_model.to_base_model())

    def create_model(self, target: Target) -> XmlModel:
        xml_model = self.xml_storage.create_model(target)
        model = XmlModel.from_base_model(xml_model)
        self._register_model(model)
        return model

    def get_or_create_model(self, target: Target) -> XmlModel:
        """
        Finds an existing Markov model for this target, or creates a new one.
        """
        model = self.get_model(target)
        if model is None:
            model = self.create_model(target)
        return model

    def get_model(self, target: Target) -> Optional[XmlModel]:
        """
        Finds an existing Markov model for this target, does not create new model.
        """
        if target.server_id not in self.models_by_server_id:
            return None
        models_by_target = self.models_by_server_id[target.server_id]
        if target not in models_by_target:
            return None
        return models_by_target[target]


# global storage instance
markov_storage = MarkovStorage()


# methods that redirect to the global instance

def load_models():
    markov_storage.load_models()


def save_model(model: Model):
    markov_storage.save_model(model)


def create_model(target: Target) -> XmlModel:
    return markov_storage.create_model(target)


def get_or_create_model(target: Target) -> XmlModel:
    return markov_storage.get_or_create_model(target)


def get_model(target: Target) -> Optional[XmlModel]:
    return markov_storage.get_model(target)
