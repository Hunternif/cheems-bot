import dataclasses
import os
from datetime import datetime, timedelta
from importlib import reload
from tempfile import TemporaryDirectory
from unittest import TestCase

from cheems import pictures
from cheems.pictures import Picture

pic1 = Picture(
    id=982459577612238869,
    url='https://discord.com/channels/975045729766764573/975045729766764578/982459577612238869',
    msg='Check this out',
    time=datetime.now(),
    uploader_id=97748578113425407,
    channel_id=975045729766764578,
    server_id=975045729766764573
)


class TestPicsDb(TestCase):
    temp_dir: TemporaryDirectory
    db_filename: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = TemporaryDirectory()
        cls.db_filename = cls.temp_dir.name + '/test_db.sqlite'

    def setUp(self) -> None:
        # Reload pictures.py to and re-initialize the db from the temp file
        pictures._con.close()
        if os.path.exists(self.db_filename):
            os.remove(self.db_filename)
        reload(pictures)
        pictures._filename = self.db_filename
        pictures._con = pictures._get_db_connection()

    @classmethod
    def tearDownClass(cls) -> None:
        pictures._con.close()
        cls.temp_dir.cleanup()

    def test_save_and_load_pic(self):
        self.assertIsNone(pictures.get_pic_by_id(123))
        pic = dataclasses.replace(pic1, msg='Check this out!;')
        pictures.save_pic(pic)
        expected_pic = dataclasses.replace(pic, msg='Check this out')
        loaded_pic = pictures.get_pic_by_id(982459577612238869)
        self.assertEqual(expected_pic, loaded_pic)

    def test_query_pics(self):
        time2 = pic1.time + timedelta(days=1)
        pic2 = dataclasses.replace(pic1, id=123, uploader_id=456, msg='Hey ya', time=time2)
        pictures.save_pic(pic1)
        pictures.save_pic(pic2)
        self.assertEqual([pic1, pic2], pictures.get_pics_where())
        self.assertEqual([pic1, pic2], pictures.get_pics_where(server_id=pic1.server_id))
        self.assertEqual([pic1, pic2], pictures.get_pics_where(channel_id=pic1.channel_id))
        self.assertEqual([pic1], pictures.get_pics_where(uploader_id=pic1.uploader_id))
        self.assertEqual([pic2], pictures.get_pics_where(uploader_id=456))
        self.assertEqual([], pictures.get_pics_where(uploader_id=0))
        self.assertEqual([pic2], pictures.get_pics_where(word='hey'))
        self.assertEqual([pic1], pictures.get_pics_where(word='THIS'))
