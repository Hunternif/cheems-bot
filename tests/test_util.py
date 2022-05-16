from unittest import TestCase

from cheems.util import sanitize_filename


class TestUtil(TestCase):
    def test_sanitize_filename(self):
        self.assertEqual('abc_5', sanitize_filename('  a.b$%c_5., '))
