import random
from typing import Any, List


class RandomUtil:
    """
    随机工具类
    提供各种随机生成的方法，包括随机元素、随机字符串、随机布尔值等
    """

    @staticmethod
    def random_ele(lst: List[Any]) -> Any:
        """
        从列表中随机选择一个元素

        Args:
            lst (List[Any]): 元素列表

        Returns:
            Any: 随机选择的元素

        Raises:
            ValueError: 如果传入的列表为空
        """
        if not lst:
            raise ValueError("列表不能为空，无法随机选择元素")
        return random.choice(lst)

    @staticmethod
    def random_string(length: int, base_string: str = "abcdefghijklmnopqrstuvwxyz0123456789") -> str:
        """
        生成指定长度的随机字符串

        Args:
            length (int): 字符串长度
            base_string (str): 基础字符集，默认为小写字母+数字

        Returns:
            str: 随机字符串

        Raises:
            ValueError: 如果长度小于等于0或基础字符集为空
        """
        if length <= 0:
            raise ValueError("字符串长度必须大于0")
        if not base_string:
            raise ValueError("基础字符集不能为空，无法生成随机字符串")
        # random.choices 批量选择字符，效率高于循环拼接
        return ''.join(random.choices(base_string, k=length))

    @staticmethod
    def random_string_upper(length: int, base_string: str = "abcdefghijklmnopqrstuvwxyz0123456789") -> str:
        """
        生成指定长度的随机大写字符串

        Args:
            length (int): 字符串长度
            base_string (str): 基础字符集，默认为小写字母+数字

        Returns:
            str: 随机大写字符串
        """
        # 复用random_string方法，减少代码冗余
        return RandomUtil.random_string(length, base_string).upper()

    @staticmethod
    def random_string_lower(length: int, base_string: str = "abcdefghijklmnopqrstuvwxyz0123456789") -> str:
        """
        生成指定长度的随机小写字符串

        Args:
            length (int): 字符串长度
            base_string (str): 基础字符集，默认为小写字母+数字

        Returns:
            str: 随机小写字符串
        """
        return RandomUtil.random_string(length, base_string).lower()

    @staticmethod
    def random_string_case(length: int, base_string: str = "abcdefghijklmnopqrstuvwxyz0123456789") -> str:
        """
        生成指定长度的随机大小写混合字符串

        Args:
            length (int): 字符串长度
            base_string (str): 基础字符集，默认为小写字母+数字

        Returns:
            str: 随机大小写混合字符串
        """
        if length <= 0:
            raise ValueError("字符串长度必须大于0")
        if not base_string:
            raise ValueError("基础字符集不能为空，无法生成随机字符串")

        content = []
        for _ in range(length):
            char = random.choice(base_string)
            # 随机决定字符的大小写
            char = char.upper() if random.randint(0, 1) == 0 else char.lower()
            content.append(char)
        return ''.join(content)

    @staticmethod
    def random_boolean() -> bool:
        """
        生成随机布尔值

        Returns:
            bool: 随机布尔值(True或False)
        """
        # 比直接转int更直观，也更符合Python的写法
        return random.choice([True, False])