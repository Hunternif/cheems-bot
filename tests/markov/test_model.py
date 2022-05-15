from datetime import datetime
from unittest import TestCase

from cheems.markov.model import Model, Row, parse_data, serialize_data


class TestMarkovModel(TestCase):
    def test_from_xml(self):
        with open('./test_model.xml') as f:
            xml_str = f.read()
        m = Model.from_xml(xml_str)
        self.assertEqual(Model(
            from_time=datetime(2022, 4, 1),
            to_time=datetime(2022, 5, 15),
            updated_time=datetime(2022, 5, 15),
            server_id=12345,
            target_id=9999,
            description="Hunternif's test data",
            data={
                'hello': Row(', my', 1),
                'my': Row('world', 2),
                'world': Row('.', 1),
            }
        ), m)

    def test_parse_data(self):
        data = parse_data('''
        hello world 1
        wow! amazing 2
        ''')
        self.assertEqual({
            'hello': Row('world', 1),
            'wow': Row('! amazing', 2),
        }, data)

    def test_serlialize_data(self):
        data_str = serialize_data({
            'hello': Row('world', 1),
            'wow': Row('! amazing', 2),
        })
        self.assertEqual('''
hello world 1
wow! amazing 2
'''.strip(), data_str)

    def test_to_xml_file(self):
        model = Model(
            from_time=datetime(2022, 4, 1),
            to_time=datetime(2022, 5, 15),
            updated_time=datetime(2022, 5, 15),
            server_id=12345,
            target_id=9999,
            description="Hunternif's test data",
            data={
                'hello': Row(', my', 1),
                'my': Row('world', 2),
                'world': Row('.', 1),
            }
        )
        serialized = model.to_xml()
        model_restored = Model.from_xml(serialized)
        self.assertEqual(model_restored, model)
