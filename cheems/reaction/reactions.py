import logging
from typing import Optional

from cheems.base_xml_data_model import BaseXmlDataModel
from cheems.config import config
from cheems.reaction.reaction_model import ReactionModel
from cheems.targets import Target
from cheems.xml_data_model_storage import XmlDataModelStorage

logger = logging.getLogger(__name__)


class ReactionStorage(XmlDataModelStorage[ReactionModel]):
    def ensure_type(self, base: BaseXmlDataModel) -> ReactionModel:
        return ReactionModel.from_base_model(base)


reaction_storage = ReactionStorage(config['reaction_model_dir'])
'''Global storage instance'''


def preload_models():
    reaction_storage.preload_models()


def create_model(target: Target) -> ReactionModel:
    return reaction_storage.create_model(target)


def get_model(target: Target) -> Optional[ReactionModel]:
    return reaction_storage.get_model(target)
