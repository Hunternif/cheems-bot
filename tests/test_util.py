from unittest import TestCase

from cheems.util import sanitize_filename, pairwise


class TestUtil(TestCase):
    def test_sanitize_filename(self):
        self.assertEqual('abc_5', sanitize_filename("  a.b$%c_5'., "))

    def test_pairwise(self):
        out = []
        for a, b in pairwise([1, 2, 3, 4, 5]):
            out.append((a, b))
        self.assertEqual([(1, 2), (2, 3), (3, 4), (4, 5)], out)

    def test_pairwise_too_short(self):
        out = []
        for a, b in pairwise([1]):
            out.append((a, b))
        self.assertEqual([], out)
