import logging
from typing import Optional

from cheems.base_xml_data_model import BaseXmlDataModel
from cheems.config import config
from cheems.markov.model import Model
from cheems.markov.model_xml import XmlModel
from cheems.targets import Target
from cheems.xml_data_model_storage import XmlDataModelStorage

logger = logging.getLogger(__name__)


class MarkovStorage(XmlDataModelStorage[XmlModel]):
    def ensure_type(self, base: BaseXmlDataModel) -> XmlModel:
        return XmlModel.from_base_model(base)


# global storage instance
markov_storage = MarkovStorage(config['markov_model_dir'])


# methods that redirect to the global instance

def preload_models():
    markov_storage.preload_models()


def load_models(load_data: bool = True):
    markov_storage.load_models(load_data)


def save_model(model: Model):
    xml_model = model if isinstance(model, XmlModel) else XmlModel.from_model(model)
    markov_storage.save_model(xml_model)


def create_model(target: Target) -> XmlModel:
    return markov_storage.create_model(target)


def get_or_create_model(target: Target) -> XmlModel:
    return markov_storage.get_or_create_model(target)


def get_model(target: Target) -> Optional[XmlModel]:
    return markov_storage.get_model(target)
