import logging
import xml.dom.minidom
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from xml.sax.saxutils import unescape

from cheems.targets import Target, User, Server, Channel, Topic

logger = logging.getLogger(__name__)

# current version of the xml format
XML_FORMAT_VERSION = 1


@dataclass
class BaseXmlDataModel:
    """
    Data structure for holding arbitrary information associated with a Target.
    The specific information is presented as a raw string. Any concrete use cases
    can further parse this string into meaningful content.
    """
    from_time: datetime
    to_time: datetime
    updated_time: datetime
    target: Target
    description: str
    raw_data: str = ''
    file_path: Optional[str] = None

    is_data_loaded: bool = True
    '''If False, data needs to be loaded from file'''

    @property
    def server_id(self) -> int:
        return self.target.server_id

    @classmethod
    def from_xml_file(cls, file_path: str, load_data: bool = True) -> 'BaseXmlDataModel':
        try:
            with open(file_path, encoding='utf-8') as f:
                xml_str = f.read()
            m = cls.from_xml(xml_str, load_data)
            m.file_path = file_path
            return m
        except Exception:
            logger.exception(f'parsing XML model: {file_path}')

    @classmethod
    def from_xml(cls, xml_str: str, load_data: bool = True) -> 'BaseXmlDataModel':
        xml = ET.fromstring(xml_str)
        format_version = int(xml.attrib['format_version'])
        if format_version >= 1:
            from_time = datetime.fromisoformat(xml.attrib['from_time']).replace(tzinfo=timezone.utc)
            to_time = datetime.fromisoformat(xml.attrib['to_time']).replace(tzinfo=timezone.utc)
            updated_time = datetime.fromisoformat(xml.attrib['updated_time']).replace(tzinfo=timezone.utc)
            description = xml.find('description').text
            if load_data:
                raw_data = xml.find('data').text.strip()
                is_data_loaded = True
            else:
                raw_data = ''
                is_data_loaded = False

            target = _target_from_xml(xml.find('target'))
        # noinspection PyUnboundLocalVariable
        return BaseXmlDataModel(from_time, to_time, updated_time, target, description, raw_data,
                                is_data_loaded=is_data_loaded)

    def to_xml(self, pretty_print: bool = True) -> str:
        root = ET.Element('model', {
            'format_version': str(XML_FORMAT_VERSION),
            'from_time': self.from_time.isoformat(' '),
            'to_time': self.to_time.isoformat(' '),
            'updated_time': self.updated_time.isoformat(' '),
        })
        _target_to_xml(root, self.target)
        ET.SubElement(root, 'description').text = self.description
        ET.SubElement(root, 'data').text = f'<![CDATA[\n{self.raw_data}\n]]>'
        raw_bytes = ET.tostring(root, 'utf-8', xml_declaration=True)
        raw_str = unescape(raw_bytes.decode())
        if pretty_print:
            dom = xml.dom.minidom.parseString(raw_str)
            return dom.toprettyxml(encoding='utf-8').decode()
        else:
            return raw_str

    def load_data(self):
        """Load data from the file"""
        if self.file_path is not None and not self.is_data_loaded:
            reloaded = BaseXmlDataModel.from_xml_file(self.file_path, load_data=True)
            self.__dict__ = reloaded.__dict__.copy()
            logger.info(f'Loaded model from file: {self.file_path}')


def _target_from_xml(tag: ET.Element) -> Target:
    """Parses target from XML format. Throws if the format is invalid"""
    t_type = tag.attrib['type']
    if t_type == User.__name__:
        return _user_from_xml(tag)
    elif t_type == Server.__name__:
        return _server_from_xml(tag)
    elif t_type == Channel.__name__:
        return _channel_from_xml(tag)
    elif t_type == Topic.__name__:
        return _topic_from_xml(tag)


def _target_to_xml(root: ET.Element, target: Target):
    """Writes the target in XML format into the given tag."""
    t_type = target.__class__.__name__
    tag = ET.SubElement(root, 'target', {'type': t_type})
    if isinstance(target, User):
        _user_to_xml(tag, target)
    elif isinstance(target, Server):
        _server_to_xml(tag, target)
    elif isinstance(target, Channel):
        _channel_to_xml(tag, target)
    elif isinstance(target, Topic):
        _topic_to_xml(tag, target)


def _user_from_xml(tag: ET.Element) -> User:
    uid = int(tag.find('id').text)
    discriminator = int(tag.find('discriminator').text)
    name = str(tag.find('name').text)
    server = _maybe_server_from_xml(tag.find('server'))
    return User(uid, name, discriminator, server)


def _user_to_xml(tag: ET.Element, user: User):
    ET.SubElement(tag, 'id').text = str(user.id)
    ET.SubElement(tag, 'discriminator').text = str(user.discriminator)
    ET.SubElement(tag, 'name').text = user.name
    if user.server is not None:
        _server_to_xml(ET.SubElement(tag, 'server'), user.server)


def _channel_from_xml(tag: ET.Element) -> Channel:
    cid = int(tag.find('id').text)
    name = str(tag.find('name').text)
    server = _maybe_server_from_xml(tag.find('server'))
    return Channel(cid, name, server)


def _channel_to_xml(tag: ET.Element, channel: Channel):
    ET.SubElement(tag, 'id').text = str(channel.id)
    ET.SubElement(tag, 'name').text = channel.name
    if channel.server is not None:
        _server_to_xml(ET.SubElement(tag, 'server'), channel.server)


def _topic_from_xml(tag: ET.Element) -> Topic:
    name = str(tag.find('name').text)
    server = _maybe_server_from_xml(tag.find('server'))
    keywords = str(tag.find('keywords').text).split(' ')
    return Topic(name, server, keywords)


def _topic_to_xml(tag: ET.Element, topic: Topic):
    ET.SubElement(tag, 'name').text = topic.name
    ET.SubElement(tag, 'keywords').text = ' '.join(topic.keywords)
    if topic.server is not None:
        _server_to_xml(ET.SubElement(tag, 'server'), topic.server)


def _server_from_xml(tag: ET.Element) -> Server:
    sid = int(tag.find('id').text)
    name = str(tag.find('name').text)
    return Server(sid, name)


def _server_to_xml(tag: ET.Element, server: Server):
    ET.SubElement(tag, 'id').text = str(server.id)
    ET.SubElement(tag, 'name').text = server.name


def _maybe_server_from_xml(tag: Optional[ET.Element]) -> Optional[Server]:
    return None if tag is None else _server_from_xml(tag)
