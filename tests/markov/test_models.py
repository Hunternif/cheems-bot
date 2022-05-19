import os
from datetime import datetime
from importlib import reload
from tempfile import TemporaryDirectory
from unittest import TestCase

from cheems.config import config
from cheems.markov import models
from cheems.markov.model import Model
from cheems.types import User, Server, Channel

# test data
time = datetime.now()
server1 = Server(100, 'London', time)
server2 = Server(200, 'Oxford', time)
channel1 = Channel(101, 'Lucky channel', time, server1)
user1 = User(123, 'Kagamin', time, 1111, server1)
user2 = User(456, 'Tsukasa', time, 2222, server2)


class TestMarkovModels(TestCase):
    temp_dir: TemporaryDirectory

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = TemporaryDirectory()
        config['markov_model_dir'] = cls.temp_dir.name

    def setUp(self) -> None:
        # Reload models.py because the directory in the config changed,
        # and to clean old references to saved models
        reload(models)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()

    def test_create_model(self):
        m = models.create_model(User(
            id=123456,
            name='Hunternif',
            discriminator=1111,
            server=Server(id=123, name='Test server', created_at=datetime.now()),
            created_at=datetime.now(),
        ))
        with open(m.file_path, 'r') as f:
            m_restored = Model.from_xml(f.read())
        self.assertEqual(m_restored, m)

    def test_create_models_dir_structure_and_reload(self):
        root = self.temp_dir.name
        data = [
            (server1, models.create_model(server1)),
            (server2, models.create_model(server2)),
            (channel1, models.create_model(channel1)),
            (user1, models.create_model(user1)),
            (user2, models.create_model(user2)),
        ]

        paths = (
            ('100 London', '100 London.xml'),
            ('200 Oxford', '200 Oxford.xml'),
            ('100 London', 'channels', '101 Lucky channel.xml'),
            ('100 London', 'users', '123 Kagamin.xml'),
            ('200 Oxford', 'users', '456 Tsukasa.xml'),
        )

        for path, (target, model) in zip(paths, data):
            self.assertEqual(os.path.join(root, *path), model.file_path)

        # clean old references
        reload(models)
        self.assertEqual(0, len(models.models))
        self.assertEqual(0, len(models.models_by_server))
        models.load_models()
        for target, model in data:
            loaded_model = models.get_model(target)
            self.assertEquals(model, loaded_model)

    def test_load_and_save_model(self):
        m = models.create_model(user1)
        self.assertEqual(user1.created_at, m.from_time)

        new_time = datetime.fromisoformat('2022-05-01')
        m.from_time = new_time
        models.save_model(m)

        reload(models)
        models.load_models()
        loaded_m = models.get_model(user1)
        self.assertEqual(new_time, loaded_m.from_time)
