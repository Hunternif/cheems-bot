from datetime import datetime
from unittest import TestCase

from cheems.markov.model import Model
from cheems.markov.models import create_model
from cheems.types import User, Server


class TestMarkovModels(TestCase):
    def test_create_model(self):
        m = create_model(User(
            id=123456,
            name='Hunternif',
            discriminator=1111,
            server=Server(id=123, name='Test server', created_at=datetime.now()),
            created_at=datetime.now(),
        ))
        with open(m.file_path, 'r') as f:
            m_restored = Model.from_xml(f.read())
        self.assertEqual(m_restored, m)
