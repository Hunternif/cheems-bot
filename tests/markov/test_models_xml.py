import os
from importlib import reload
from tempfile import TemporaryDirectory
from unittest import TestCase

from cheems.config import config
from cheems.markov import models_xml
from cheems.markov.model_xml import XmlModel
from cheems.types import User, Server, Channel

# test data
server1 = Server(100, 'London')
server2 = Server(200, 'Oxford')
channel1 = Channel(101, 'Lucky channel', server1)
user1 = User(123, 'Kagamin', 1111, server1)
user2 = User(456, 'Tsukasa', 2222, server2)


class TestMarkovModelsXml(TestCase):
    temp_dir: TemporaryDirectory

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = TemporaryDirectory()
        config['markov_model_dir'] = cls.temp_dir.name

    def setUp(self) -> None:
        # Reload models_xml.py because the directory in the config changed,
        # and to clean old references to saved models
        reload(models_xml)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()

    def test_create_model(self):
        m = models_xml.create_model(User(
            id=123456,
            name='Hunternif',
            discriminator=1111,
            server=Server(id=123, name='Test server'),
        ))
        models_xml.save_model(m)
        m_restored = XmlModel.from_xml_file(m.file_path)
        self.assertEqual(m_restored, m)

    def test_create_models_dir_structure_and_reload(self):
        root = self.temp_dir.name
        data = [
            (server1, models_xml.create_model(server1)),
            (server2, models_xml.create_model(server2)),
            (channel1, models_xml.create_model(channel1)),
            (user1, models_xml.create_model(user1)),
            (user2, models_xml.create_model(user2)),
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
            models_xml.save_model(model)

        # clean old references
        reload(models_xml)
        self.assertEqual(0, len(models_xml.models))
        self.assertEqual(0, len(models_xml.models_by_server_id))
        models_xml.load_models()
        for target, model in data:
            loaded_model = models_xml.get_model(target)
            self.assertEquals(model, loaded_model)

    def test_load_and_save_model(self):
        m = models_xml.create_model(user1)
        self.assertEqual(user1.id, m.target.id)
        self.assertEqual({}, m.data)

        m.append_word_pair('hello', 'world')
        self.assertEqual({'hello': {'world': 1}}, m.data)
        models_xml.save_model(m)

        reload(models_xml)
        models_xml.load_models()
        loaded_m = models_xml.get_model(user1)
        self.assertEqual({'hello': {'world': 1}}, loaded_m.data)
