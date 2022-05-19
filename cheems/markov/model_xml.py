import logging

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from cheems.markov.model import Model

logger = logging.getLogger(__name__)

# current version of the xml format
XML_FORMAT_VERSION = 1


@dataclass
class XmlModel:
    model: Model
    file_path: Optional[str] = None

    @classmethod
    def from_xml_file(cls, file_path: str) -> 'XmlModel':
        with open(file_path, encoding='utf-8') as f:
            xml_str = f.read()
        m = cls.from_xml(xml_str)
        m.file_path = file_path
        return m

    @classmethod
    def from_xml(cls, xml_str: str) -> 'XmlModel':
        try:
            xml = ET.fromstring(xml_str)
            format_version = int(xml.attrib['format_version'])
            if format_version >= 1:
                from_time = datetime.fromisoformat(xml.attrib['from_time'])
                to_time = datetime.fromisoformat(xml.attrib['to_time'])
                updated_time = datetime.fromisoformat(xml.attrib['updated_time'])
                server_id = int(xml.attrib['server_id'])
                target_id = int(xml.attrib['target_id'])
                description = xml.attrib['description']
                data = Model.parse_data(xml.text)
            # noinspection PyUnboundLocalVariable
            m = Model(from_time, to_time, updated_time, server_id, target_id, description, data)
            return XmlModel(m)
        except Exception:
            logger.exception(f'parsing XML model {xml_str}')

    def to_xml(self) -> str:
        root = ET.Element('model', {
            'format_version': str(XML_FORMAT_VERSION),
            'from_time': self.model.from_time.isoformat(' '),
            'to_time': self.model.to_time.isoformat(' '),
            'updated_time': self.model.updated_time.isoformat(' '),
            'server_id': str(self.model.server_id),
            'target_id': str(self.model.target_id),
            'description': self.model.description,
        })
        root.text = f'\n{Model.serialize_data(self.model.data)}\n'
        raw_str = ET.tostring(root, 'utf-8', xml_declaration=True)
        return bytes.decode(raw_str)