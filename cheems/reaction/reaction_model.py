import random
from dataclasses import dataclass, field

from cheems.base_xml_data_model import BaseXmlDataModel
from cheems.config import config

ReactModelData = dict[str, int]
'''
Stores reaction names and occurrence values, e.g.:
:thumbsup: 10
:trollface: 999
'''


@dataclass
class ReactionModel(BaseXmlDataModel):
    """
    Stored in XML.
    """
    data: ReactModelData = field(default_factory=dict)

    @classmethod
    def from_base_model(cls, xml_model: BaseXmlDataModel) -> 'ReactionModel':
        data = ReactionModel.parse_data(xml_model.raw_data)
        fields = xml_model.__dict__.copy()
        fields['raw_data'] = ''  # delete the raw string to save memory
        return cls(**fields, data=data)

    @classmethod
    def from_xml_file(cls, file_path: str, load_data: bool = True) -> 'ReactionModel':
        xml_model = BaseXmlDataModel.from_xml_file(file_path, load_data)
        return cls.from_base_model(xml_model)

    @classmethod
    def from_xml(cls, xml_str: str, load_data: bool = True) -> 'ReactionModel':
        xml_model = BaseXmlDataModel.from_xml(xml_str, load_data)
        return cls.from_base_model(xml_model)

    def to_xml(self, pretty_print: bool = True) -> str:
        self.raw_data = self.serialize_data()
        output = super().to_xml(pretty_print)
        self.raw_data = ''  # delete the raw string to save memory
        return output

    @classmethod
    def parse_data(cls, text: str) -> ReactModelData:
        data: ReactModelData = {}
        max_weight = config.get('reaction_model_max_weight', 9999)
        for line in text.strip().splitlines():
            (reaction, count) = line.strip().split(' ')
            weight = min(int(count), max_weight)  # limit weight
            data[reaction] = weight
        return data

    def load_data(self):
        super().load_data()
        self.data = ReactionModel.parse_data(self.raw_data)

    def serialize_data(self) -> str:
        lines: list[str] = []
        for reaction, count in self.data.items():
            lines.append(f'{reaction} {count}')
        return '\n'.join(sorted(lines))

    def get_random_reaction(self) -> str:
        """Weighted according to data"""
        return random.choices(list(self.data.keys()), list(self.data.values()))[0]
