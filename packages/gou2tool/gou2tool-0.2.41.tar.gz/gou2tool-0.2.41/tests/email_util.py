# 0597-...webmaster@xmrc.com.cn
import unittest

from gou2tool.util import EmailUtil


class TestDemo(unittest.TestCase):
    def test_simple_uuid(self):
        print(EmailUtil.is_email("0597-...webmaster@xmrc.com.cn"))
        print(EmailUtil.is_email("wl4837@163.com"))
        print(EmailUtil.is_email("daa@163.com"))
        print(EmailUtil.is_email("daa3.com"))
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()