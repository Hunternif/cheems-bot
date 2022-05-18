from datetime import datetime, timedelta
from unittest import TestCase

from multidict import MultiDict

from cheems.markov.model import Model, Row, parse_data, serialize_data


def create_test_model(
        data_str: str = '',
        server_id: int = 123,
        target_id: int = 456,
        description: str = 'Test model',
) -> Model:
    return Model(
        from_time=datetime.now() - timedelta(days=1),
        to_time=datetime.now(),
        updated_time=datetime.now(),
        server_id=server_id,
        target_id=target_id,
        description=description,
        data=parse_data(data_str)
    )


class TestMarkovModel(TestCase):
    def test_from_xml(self):
        with open('./tests/markov/test_model.xml') as f:
            xml_str = f.read()
        m = Model.from_xml(xml_str)
        self.assertEqual(Model(
            from_time=datetime(2022, 4, 1),
            to_time=datetime(2022, 5, 15),
            updated_time=datetime(2022, 5, 15),
            server_id=12345,
            target_id=9999,
            description="Hunternif's test data",
            data=MultiDict([
                ('hello', Row(',my', 1)),
                ('my', Row('world', 2)),
                ('world', Row('.', 1)),
            ])
        ), m)

    def test_parse_data(self):
        data = parse_data('''
        hello world 1
        wow! amazing 2
        ''')
        self.assertEqual({
            'hello': Row('world', 1),
            'wow!': Row('amazing', 2),
        }, data)

    def test_parse_data_with_duplicates(self):
        data = parse_data('''
        hello world 1
        hello darkness 2
        world . 1
        ''')
        self.assertEqual(MultiDict([
            ('hello', Row('world', 1)),
            ('hello', Row('darkness', 2)),
            ('world', Row('.', 1)),
        ]), data)

    def test_serlialize_data(self):
        data_str = serialize_data(MultiDict([
            ('hello', Row('world', 1)),
            ('wow!', Row('amazing', 2)),
        ]))
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
                'hello': Row(',my', 1),
                'my': Row('world', 2),
                'world': Row('.', 1),
            }
        )
        serialized = model.to_xml()
        model_restored = Model.from_xml(serialized)
        self.assertEqual(model_restored, model)
