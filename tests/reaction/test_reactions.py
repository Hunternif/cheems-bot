import random
from datetime import datetime, timezone
from unittest import TestCase

from cheems.reaction import reactions
from cheems.reaction.reaction_model import ReactionModel

from cheems.targets import Server, User

# test data
test_server = Server(12345, 'Test server')
test_model = ReactionModel(
    from_time=datetime(2022, 4, 1, tzinfo=timezone.utc),
    to_time=datetime(2022, 5, 15, tzinfo=timezone.utc),
    updated_time=datetime(2022, 5, 15, tzinfo=timezone.utc),
    target=User(9999, 'Hunternif', 8888, test_server),
    description="Hunternif's test reaction data",
    data={
        '🤔': 2,
        '👍': 1,
    }
)


class TestReactions(TestCase):
    def test_parse_data(self):
        data = ReactionModel.parse_data('''
🤔 5
<:cheems:1140041467432271952> 3
        ''')
        self.assertEqual({
            '🤔': 5,
            '<:cheems:1140041467432271952>': 3,
        }, data)

    def test_from_xml(self):
        with open('./tests/reaction/test_react_model.xml') as f:
            xml_str = f.read()
        m = ReactionModel.from_xml(xml_str)
        self.assertEqual(Server(), m)

    def test_weighted_random_reaction(self):
        model = reactions.create_model(test_server)
        model.data = {'one': 1, 'two': 10, }

        count_one = 0
        count_two = 0
        for x in range(100):
            random.seed(x)
            s = model.get_random_reaction()
            if s == 'one':
                count_one += 1
            elif s == 'two':
                count_two += 1
        self.assertGreater(count_two, count_one * 5)
