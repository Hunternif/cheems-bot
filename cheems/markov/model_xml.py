import logging
from dataclasses import dataclass
from typing import Optional

from cheems.base_xml_data_model import BaseXmlDataModel
from cheems.markov.model import Model

logger = logging.getLogger(__name__)


@dataclass
class XmlModel(Model):
    """
    Markov chain model which is serialized specifically to a XML file.
    """
    file_path: Optional[str] = None

    def __hash__(self) -> int:
        return hash(self.target)

    @classmethod
    def from_model(cls, model: Model, file_path: str = None) -> 'XmlModel':
        return cls(**model.__dict__, file_path=file_path)

    @classmethod
    def from_base_model(cls, xml_model: BaseXmlDataModel) -> 'XmlModel':
        data = Model.parse_data(xml_model.raw_data)
        fields = xml_model.__dict__.copy()
        del fields['raw_data']
        return cls(**fields, data=data)

    @classmethod
    def from_xml_file(cls, file_path: str) -> 'XmlModel':
        with open(file_path, encoding='utf-8') as f:
            xml_str = f.read()
        m = cls.from_xml(xml_str)
        m.file_path = file_path
        return m

    @classmethod
    def from_xml(cls, xml_str: str) -> 'XmlModel':
        xml_model = BaseXmlDataModel.from_xml(xml_str)
        return XmlModel.from_base_model(xml_model)

    def to_base_model(self) -> BaseXmlDataModel:
        raw_data = self.serialize_data()
        fields = self.__dict__.copy()
        del fields['data']
        return BaseXmlDataModel(**fields, raw_data=raw_data)

    def to_xml(self, pretty_print: bool = True) -> str:
        return self.to_base_model().to_xml(pretty_print)
