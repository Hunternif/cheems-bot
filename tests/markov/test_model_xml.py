import unittest
from datetime import datetime

from cheems.markov.model import Model
from cheems.markov.model_xml import XmlModel


class TestMarkovXmlModel(unittest.TestCase):
    def test_from_xml(self):
        with open('./tests/markov/test_model.xml') as f:
            xml_str = f.read()
        m = XmlModel.from_xml(xml_str)
        self.assertEqual(XmlModel(Model(
            from_time=datetime(2022, 4, 1),
            to_time=datetime(2022, 5, 15),
            updated_time=datetime(2022, 5, 15),
            server_id=12345,
            target_id=9999,
            description="Hunternif's test data",
            data={
                'hello': {',my': 1},
                'my': {'world': 2},
                'world': {'.': 1},
            }
        )), m)

    def test_to_xml_file(self):
        model = XmlModel(Model(
            from_time=datetime(2022, 4, 1),
            to_time=datetime(2022, 5, 15),
            updated_time=datetime(2022, 5, 15),
            server_id=12345,
            target_id=9999,
            description="Hunternif's test data",
            data={
                'hello': {',my': 1},
                'my': {'world': 2},
                'world': {'.': 1},
            }
        ))
        serialized = model.to_xml()
        model_restored = XmlModel.from_xml(serialized)
        self.assertEqual(model_restored, model)
