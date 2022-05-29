import dataclasses
import unittest
from datetime import datetime

from cheems.markov.model_xml import XmlModel
from cheems.targets import User, Server, Channel, Topic

test_server = Server(12345, 'Test server')
test_model = XmlModel(
    from_time=datetime(2022, 4, 1),
    to_time=datetime(2022, 5, 15),
    updated_time=datetime(2022, 5, 15),
    target=User(9999, 'Hunternif', 8888, test_server),
    description="Hunternif's test data",
    data={
        'hello': {',my': 1},
        'my': {'world': 2},
        'world': {'.': 1},
    }
)


class TestMarkovXmlModel(unittest.TestCase):
    def test_from_xml(self):
        with open('./tests/markov/test_model.xml') as f:
            xml_str = f.read()
        m = XmlModel.from_xml(xml_str)
        self.assertEqual(test_model, m)

    def test_user_model_to_xml_file(self):
        model = test_model
        serialized = model.to_xml()
        model_restored = XmlModel.from_xml(serialized)
        self.assertEqual(model, model_restored)

    def test_server_model_xml_file(self):
        model = dataclasses.replace(test_model, target=test_server)
        serialized = model.to_xml()
        model_restored = XmlModel.from_xml(serialized)
        self.assertEqual(model, model_restored)

    def test_channel_model_xml_file(self):
        model = dataclasses.replace(
            test_model,
            target=Channel(200, 'Lucky channel', test_server)
        )
        serialized = model.to_xml()
        model_restored = XmlModel.from_xml(serialized)
        self.assertEqual(model, model_restored)

    def test_topic_model_xml_file(self):
        model = dataclasses.replace(
            test_model,
            target=Topic('Genshin', test_server, ['genshin', 'геншин', 'гейщит'])
        )
        serialized = model.to_xml()
        model_restored = XmlModel.from_xml(serialized)
        self.assertEqual(model, model_restored)
