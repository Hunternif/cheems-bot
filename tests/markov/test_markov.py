import random
from unittest import TestCase

# noinspection PyProtectedMember
from cheems.markov.markov import markov_chain, _pick_first_word, _break_into_words, train_model_on_sentence
from tests.markov.test_model import create_test_model


class TestMarkovChain(TestCase):
    def test_single_chain(self):
        model = create_test_model('''
hello ,my 1
my world 1
world . 1
        ''')
        s = markov_chain(model, 'hello')
        self.assertEqual('hello, my world.', s)

    def test_various_ends(self):
        model = create_test_model('''
hello ,world 1
world ! 1
        ''')
        s = markov_chain(model, 'hello')
        self.assertEqual('hello, world!', s)

    def test_model_without_end(self):
        model = create_test_model('''
hello ,my 1
my world 1
        ''')
        s = markov_chain(model, 'hello')
        self.assertEqual('hello, my world.', s)

    def test_weighted_chain(self):
        model = create_test_model('''
hello world 1
hello darkness 10
        ''')
        count_world = 0
        count_darkness = 0
        for x in range(100):
            random.seed(x)
            s = markov_chain(model, 'hello')
            if s == 'hello world.':
                count_world += 1
            elif s == 'hello darkness.':
                count_darkness += 1
        self.assertGreater(count_darkness, count_world * 5)

    def test_limit(self):
        model = create_test_model('''
hello hello 1
        ''')
        s = markov_chain(model, 'hello', limit=4)
        self.assertEqual('hello hello hello hello', s)

    def test_empty_input(self):
        model = create_test_model('''
hello ,my 1
my world 1
world . 1
        ''')
        random.seed(1)
        s = markov_chain(model, '  ')
        self.assertEqual('hello, my world.', s)

    def test_empty_model(self):
        model = create_test_model('')
        random.seed(1)
        s = markov_chain(model)
        self.assertEqual('', s)

    def test_pick_first_word_prefers_non_END(self):
        # model without END
        model = create_test_model('''
first second 1
second something 1
        ''')
        random.seed(5)
        w = _pick_first_word(model)
        self.assertEqual('second', w)
        # modify the model so that the same row now has END
        model = create_test_model('''
first second 1
second . 1
        ''')
        random.seed(5)
        w = _pick_first_word(model)
        self.assertEqual('first', w)

    def test_pick_first_word_picks_something_even_END(self):
        model = create_test_model('''
first . 1
second . 1
            ''')
        random.seed(2)
        w = _pick_first_word(model)
        self.assertEqual('first', w)

    def test_break_into_words(self):
        words = _break_into_words(
            ' Hello, darkness   ,,\n my   old friend?! I... go \n home'
        )
        self.assertEqual([
            'Hello', ',darkness', ',my', 'old', 'friend', '?', 'I', '.', 'go', '.', 'home'
        ], words)

    def test_train_model(self):
        model = create_test_model('''
hello ,my 1
my world 2
world . 1
        ''')
        train_model_on_sentence(model, 'hello my world, dude')
        self.assertEqual('''
dude . 1
hello ,my 1
hello my 1
my world 3
world ,dude 1
world . 1
'''.strip(), model.serialize_data())

    def test_train_empty_model(self):
        model = create_test_model('')
        train_model_on_sentence(model, 'hello, my dude')
        self.assertEqual('''
dude . 1
hello ,my 1
my dude 1
'''.strip(), model.serialize_data())

    def test_train_model_on_single_world(self):
        model = create_test_model('')
        train_model_on_sentence(model, 'hello')
        self.assertEqual('''
hello . 1
'''.strip(), model.serialize_data())

    def test_train_model_on_two_sentences(self):
        model = create_test_model('''
hello ,my 1
my world 2
world . 1
        ''')
        train_model_on_sentence(model, 'my friends! my world')
        self.assertEqual('''
friends ! 1
hello ,my 1
my friends 1
my world 3
world . 2
'''.strip(), model.serialize_data())
