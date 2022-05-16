import logging
import typing
from datetime import datetime
import xml.etree.ElementTree as ET

from attr import define
from multidict import MultiDict

logger = logging.getLogger(__name__)

# current version of the xml format
XML_FORMAT_VERSION = 1
# this character indicates end of a sentence
END = '.'

# 'next_word' will include punctuation attached to the preceding world, e.g. 'hello' - ',my'
Row = typing.NamedTuple('Row', [
    ('next_word', str),
    ('count', int)
])


def parse_data(text: str) -> MultiDict[Row]:
    data: MultiDict[Row] = MultiDict()
    for line in text.strip().splitlines():
        (first_word, next_word, count) = line.strip().split(' ')
        data.add(first_word, Row(next_word, int(count)))
    return data


def serialize_data(data: MultiDict[Row]) -> str:
    lines = []
    for first_word, row in data.items():
        next_word = row.next_word
        count = row.count
        lines.append(f'{first_word} {next_word} {count}')
    return '\n'.join(lines)


@define(slots=False)
class Model:
    from_time: datetime
    to_time: datetime
    updated_time: datetime
    server_id: int
    target_id: int
    description: str
    data: MultiDict[Row] = MultiDict()

    @classmethod
    def from_xml(cls, xml_str: str) -> 'Model':
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
                data = parse_data(xml.text)
            # noinspection PyUnboundLocalVariable
            return Model(from_time, to_time, updated_time, server_id, target_id, description, data)
        except Exception:
            logger.exception(f'parsing model {xml_str}')

    def to_xml(self) -> str:
        root = ET.Element('model', {
            'format_version': str(XML_FORMAT_VERSION),
            'from_time': self.from_time.isoformat(' '),
            'to_time': self.to_time.isoformat(' '),
            'updated_time': self.updated_time.isoformat(' '),
            'server_id': str(self.server_id),
            'target_id': str(self.target_id),
            'description': self.description,
        })
        root.text = f'\n{serialize_data(self.data)}\n'
        raw_str = ET.tostring(root, 'utf-8', xml_declaration=True)
        return bytes.decode(raw_str)
