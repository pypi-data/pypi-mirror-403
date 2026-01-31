import datetime
from typing import Optional, Union


class DateUtil:
    """
    日期时间工具类
    提供标准化的日期时间格式化、日期获取、日期判断等功能，兼容秒级/微秒级时间戳、日期字符串输入。

    字段说明:
    - 支持时区切换（默认Asia/Shanghai）
    - 支持微秒(u)、毫秒(v)格式符替换
    - 兼容PHP日期格式的核心转换（Y/m/d/H/i/s等）
    """

    @staticmethod
    def date(
            input: Optional[Union[int, float, str, None]] = None,
            format: str = 'Y-m-d H:i:s',
            timezone: str = 'Asia/Shanghai'
    ) -> str:
        """
        格式化日期时间，支持时间戳、日期字符串、空值输入，兼容微秒/毫秒格式符
        :param input: 时间戳（秒级/微秒级）、日期字符串或None（默认当前时间）
        :param format: 日期格式（支持PHP格式符，u=微秒，v=毫秒）
        :param timezone: 时区（默认Asia/Shanghai）
        :return: 格式化后的日期时间字符串
        """
        # 1. 设置时区
        tz = datetime.timezone(datetime.timedelta(hours=8))  # Asia/Shanghai = UTC+8
        try:
            # 兼容其他时区（简化实现，核心支持上海时区）
            if timezone != 'Asia/Shanghai':
                tz_offset = int(timezone.split('/')[-1]) if 'UTC' not in timezone else 0
                tz = datetime.timezone(datetime.timedelta(hours=tz_offset))
        except:
            tz = datetime.timezone(datetime.timedelta(hours=8))

        # 2. 处理输入参数，转换为datetime对象（包含微秒信息）
        now = datetime.datetime.now(tz)
        target_datetime: datetime.datetime
        fraction: float = 0.0  # 微秒/毫秒小数部分（输入值的小数部分）

        if input is None:
            # 无输入：使用当前时间（包含微秒）
            target_datetime = now
            fraction = target_datetime.microsecond / 1000000.0
        elif isinstance(input, str) and not input.replace('.', '').isdigit():
            # 输入是日期字符串：转换为datetime对象
            try:
                # 尝试解析常见日期格式
                # 直接实现PHP格式符转换为Python格式符
                format_mapping = {
                    'Y': '%Y',  # 4位年份
                    'm': '%m',  # 2位月份（补零）
                    'd': '%d',  # 2位日期（补零）
                    'H': '%H',  # 24小时制（补零）
                    'i': '%M',  # 分钟（补零）
                    's': '%S',  # 秒（补零）
                    'y': '%y',  # 2位年份
                    'j': '%d',  # 日期（不补零，Python无直接对应，用%d兼容）
                }

                python_format = format
                for php_char, py_char in format_mapping.items():
                    python_format = python_format.replace(php_char, py_char)

                parsed_dt = datetime.datetime.strptime(input, python_format)
                target_datetime = parsed_dt.replace(tzinfo=tz)
                fraction = 0.0
            except (ValueError, TypeError):
                # 解析失败：使用当前时间
                target_datetime = now
                fraction = target_datetime.microsecond / 1000000.0
        else:
            # 输入是数字（时间戳：秒级/微秒级）
            input_num = float(input)
            if input_num < 10000000000:  # 秒级时间戳（10位以内，含小数秒）
                seconds = int(input_num)
                fraction = input_num - seconds
            else:  # 微秒级时间戳（13位以上，转换为秒+微秒）
                seconds = int(input_num / 1000000)
                fraction = (input_num / 1000000) - seconds

            # 转换为datetime对象（包含时区）
            target_datetime = datetime.datetime.fromtimestamp(seconds, tz=tz)

        # 3. 处理微秒(u)和毫秒(v)格式符替换
        # 直接实现PHP格式符转换为Python格式符
        format_mapping = {
            'Y': '%Y',  # 4位年份
            'm': '%m',  # 2位月份（补零）
            'd': '%d',  # 2位日期（补零）
            'H': '%H',  # 24小时制（补零）
            'i': '%M',  # 分钟（补零）
            's': '%S',  # 秒（补零）
            'y': '%y',  # 2位年份
            'j': '%d',  # 日期（不补零，Python无直接对应，用%d兼容）
        }

        python_format = format
        for php_char, py_char in format_mapping.items():
            python_format = python_format.replace(php_char, py_char)
        final_format = python_format

        if 'u' in format:
            # 微秒：6位补零
            microseconds = int(round(fraction * 1000000))
            microsec_formatted = f"{microseconds:06d}"
            final_format = final_format.replace('u', microsec_formatted)

        if 'v' in format:
            # 毫秒：3位补零
            milliseconds = int(round(fraction * 1000))
            millisec_formatted = f"{milliseconds:03d}"
            final_format = final_format.replace('v', millisec_formatted)

        # 4. 格式化输出（移除未转换的格式符，保证结果整洁）
        try:
            result = target_datetime.strftime(final_format)
        except:
            # 格式符兼容失败：使用默认格式兜底
            result = target_datetime.strftime('%Y-%m-%d %H:%M:%S')

        return result

    @staticmethod
    def date_cn(microtime: Optional[Union[int, float, None]] = None) -> str:
        """
        格式化中文日期时间（年/月/日/时/分/秒）
        :param microtime: 时间戳或None
        :return: 中文格式化日期字符串
        """
        return DateUtil.date(microtime, 'Y年m月d日 H时i分s秒', 'Asia/Shanghai')

    @staticmethod
    def now(format: str = 'Y-m-d H:i:s') -> str:
        """
        获取当前时间格式化字符串
        :param format: 日期格式
        :return: 格式化后的当前时间
        """
        return DateUtil.date(None, format)

    @staticmethod
    def now_cn() -> str:
        """
        获取当前时间的中文格式化字符串
        :return: 中文格式化当前时间
        """
        return DateUtil.date(None, 'Y年m月d日 H时i分s秒')

    @staticmethod
    def short_year(timestamp: Optional[Union[int, float, None]] = None) -> str:
        """
        获取2位年份（年份后两位）
        :param timestamp: 时间戳或None
        :return: 2位年份字符串
        """
        return DateUtil.date(timestamp, 'y')

    @staticmethod
    def first_day_of_month(
            year: Optional[int] = None,
            month: Optional[int] = None,
            format: str = 'Y-m-d'
    ) -> str:
        """
        获取指定月份的第一天
        :param year: 年份（默认当前年份）
        :param month: 月份（默认当前月份）
        :param format: 日期格式
        :return: 月份第一天的格式化字符串
        """
        current_dt = datetime.datetime.now()
        target_year = year if year is not None else current_dt.year
        target_month = month if month is not None else current_dt.month

        first_day = datetime.datetime(target_year, target_month, 1)
        return DateUtil.date(first_day.timestamp(), format)

    @staticmethod
    def last_day_of_month(
            year: Optional[int] = None,
            month: Optional[int] = None,
            format: str = 'Y-m-d'
    ) -> str:
        """
        获取指定月份的最后一天
        :param year: 年份（默认当前年份）
        :param month: 月份（默认当前月份）
        :param format: 日期格式
        :return: 月份最后一天的格式化字符串
        """
        current_dt = datetime.datetime.now()
        target_year = year if year is not None else current_dt.year
        target_month = month if month is not None else current_dt.month

        # 计算下一个月的第一天，再减一天得到当前月最后一天
        next_month = target_month + 1
        next_year = target_year
        if next_month > 12:
            next_month = 1
            next_year += 1

        last_day = datetime.datetime(next_year, next_month, 1) - datetime.timedelta(days=1)
        return DateUtil.date(last_day.timestamp(), format)

    @staticmethod
    def first_day_of_year(
            year: Optional[int] = None,
            format: str = 'Y-m-d'
    ) -> str:
        """
        获取指定年份的第一天
        :param year: 年份（默认当前年份）
        :param format: 日期格式
        :return: 年份第一天的格式化字符串
        """
        current_dt = datetime.datetime.now()
        target_year = year if year is not None else current_dt.year

        first_day = datetime.datetime(target_year, 1, 1)
        return DateUtil.date(first_day.timestamp(), format)

    @staticmethod
    def last_day_of_year(
            year: Optional[int] = None,
            format: str = 'Y-m-d'
    ) -> str:
        """
        获取指定年份的最后一天
        :param year: 年份（默认当前年份）
        :param format: 日期格式
        :return: 年份最后一天的格式化字符串
        """
        current_dt = datetime.datetime.now()
        target_year = year if year is not None else current_dt.year

        last_day = datetime.datetime(target_year, 12, 31)
        return DateUtil.date(last_day.timestamp(), format)

    @staticmethod
    def first_day_of_week(
            year: Optional[int] = None,
            week: Optional[int] = None,
            format: str = 'Y-m-d'
    ) -> str:
        """
        获取指定周的第一天（周一）
        :param year: 年份（默认当前年份）
        :param week: 周数（默认当前周）
        :param format: 日期格式
        :return: 周第一天的格式化字符串
        """
        current_dt = datetime.datetime.now()
        target_year = year if year is not None else current_dt.year
        target_week = week if week is not None else current_dt.isocalendar()[1]

        # 计算指定周的周一
        first_day_of_year = datetime.datetime(target_year, 1, 1)
        # 计算年第一天是周几（ISO：周一=1，周日=7）
        first_weekday = first_day_of_year.isocalendar()[2]
        # 计算第一周的偏移量
        days_offset = (target_week - 1) * 7 - (first_weekday - 1)
        first_day_of_week = first_day_of_year + datetime.timedelta(days=days_offset)

        return DateUtil.date(first_day_of_week.timestamp(), format)

    @staticmethod
    def last_day_of_week(
            year: Optional[int] = None,
            week: Optional[int] = None,
            format: str = 'Y-m-d'
    ) -> str:
        """
        获取指定周的最后一天（周日）
        :param year: 年份（默认当前年份）
        :param week: 周数（默认当前周）
        :param format: 日期格式
        :return: 周最后一天的格式化字符串
        """
        first_day = DateUtil.first_day_of_week(year, week, format)

        # 直接实现PHP格式符转换为Python格式符
        format_mapping = {
            'Y': '%Y',  # 4位年份
            'm': '%m',  # 2位月份（补零）
            'd': '%d',  # 2位日期（补零）
            'H': '%H',  # 24小时制（补零）
            'i': '%M',  # 分钟（补零）
            's': '%S',  # 秒（补零）
            'y': '%y',  # 2位年份
            'j': '%d',  # 日期（不补零，Python无直接对应，用%d兼容）
        }

        python_format = format
        for php_char, py_char in format_mapping.items():
            python_format = python_format.replace(php_char, py_char)

        # 转换为datetime对象，加6天得到周日
        first_day_dt = datetime.datetime.strptime(first_day, python_format)
        last_day_dt = first_day_dt + datetime.timedelta(days=6)

        return DateUtil.date(last_day_dt.timestamp(), format)

    @staticmethod
    def today_number(with_leading_zero: bool = True) -> str:
        """
        获取今天的日期号码
        :param with_leading_zero: 是否补零（默认True）
        :return: 日期号码字符串
        """
        format_char = 'd' if with_leading_zero else 'j'
        return DateUtil.date(None, format_char)

    @staticmethod
    def day_number(
            timestamp: Optional[Union[int, float, None]] = None,
            with_leading_zero: bool = True
    ) -> str:
        """
        获取指定时间戳的日期号码
        :param timestamp: 时间戳（默认当前时间）
        :param with_leading_zero: 是否补零（默认True）
        :return: 日期号码字符串
        """
        format_char = 'd' if with_leading_zero else 'j'
        return DateUtil.date(timestamp, format_char)

    @staticmethod
    def is_today(  # 修正原PHP方法名拼写：isToDay -> is_today（遵循Python命名规范）
            date: Optional[Union[int, float, str, None]] = None,
            format: str = 'Y-m-d'
    ) -> bool:
        """
        判断指定日期是否为今天
        :param date: 日期字符串、时间戳或None（默认当前时间）
        :param format: 日期格式
        :return: 是否为今天（bool）
        """
        today = DateUtil.date(None, format)
        check_date = DateUtil.date(date, format)

        return today == check_date

    @staticmethod
    def is_yesterday(
            date: Optional[Union[int, float, str, None]] = None,
            format: str = 'Y-m-d'
    ) -> bool:
        """
        判断指定日期是否为昨天
        :param date: 日期字符串、时间戳或None（默认当前时间）
        :param format: 日期格式
        :return: 是否为昨天（bool）
        """
        yesterday_dt = datetime.datetime.now() - datetime.timedelta(days=1)
        yesterday = DateUtil.date(yesterday_dt.timestamp(), format)
        check_date = DateUtil.date(date, format)

        return yesterday == check_date
