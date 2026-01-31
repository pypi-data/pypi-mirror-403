import unittest

from gou2tool.core.response import R


class TestDemo(unittest.TestCase):

    def test_is_phone(self):
        print(R.ok())
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()