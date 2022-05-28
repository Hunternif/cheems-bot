from datetime import datetime, timedelta
from unittest import TestCase

from cheems.markov.model import Model
from cheems.types import Target


def create_test_model(
        data_str: str = '',
        server_id: int = 123,
        target: Target = Target(0, 'test target'),
        description: str = 'Test model',
) -> Model:
    return Model(
        from_time=datetime.now() - timedelta(days=1),
        to_time=datetime.now(),
        updated_time=datetime.now(),
        server_id=server_id,
        target=target,
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

    def test_serlialize_data_sorted(self):
        data_str = Model._serialize_data({
            'world': {'.': 1},
            'hello': {
                'alpha': 4,
                ',my': 1,
                'darkness': 2,
            },
            'my': {'world': 3},
        })
        self.assertEqual('''
hello ,my 1
hello alpha 4
hello darkness 2
my world 3
world . 1
'''.strip(), data_str)

