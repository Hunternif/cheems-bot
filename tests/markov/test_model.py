from datetime import datetime, timedelta
from unittest import TestCase

from cheems.markov.model import Model


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
        data=Model.parse_data(data_str)
    )


class TestMarkovModel(TestCase):
    def test_parse_data(self):
        data = Model.parse_data('''
        hello world 1
        wow! amazing 2
        ''')
        self.assertEqual({
            'hello': {'world': 1},
            'wow!': {'amazing': 2},
        }, data)

    def test_parse_data_with_duplicates(self):
        data = Model.parse_data('''
        hello world 1
        hello darkness 2
        world . 1
        ''')
        self.assertCountEqual({
            'hello': {
                ',my': 1,
                'darkness': 2,
            },
            'world': {'.': 1},
        }, data)

    def test_serlialize_data(self):
        data_str = Model.serialize_data({
            'hello': {'world': 1},
            'wow!': {'amazing': 2},
        })
        self.assertEqual('''
hello world 1
wow! amazing 2
'''.strip(), data_str)
