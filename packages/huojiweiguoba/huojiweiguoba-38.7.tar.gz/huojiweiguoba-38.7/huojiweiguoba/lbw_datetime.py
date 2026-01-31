import datetime
import time
from typing import Literal

def get_local_now_date():
    '''获取电脑当前时间'''
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def update_date(date,cycle:Literal['days','minutes','seconds','hours'],num,format='%Y-%m-%d %H:%M:%S'):
    '''
    日期增加或者减少 天 分 秒 时
    :date 日期
    :cycle ['days','minutes','seconds','hours']
    :num 增加或者减少的数量 +1 -1
    '''
    now = datetime.datetime.strptime(date, format)
    date = (now + datetime.timedelta(**{cycle:num})).strftime(format)
    return date
def datetime_to_timestamp_milliseconds(datetime_str):
    """
    将日期时间字符串转换为毫秒级时间戳

    参数:
    datetime_str: 日期时间字符串，格式如 "2026-01-20 10:39"

    返回:
    int: 毫秒级时间戳
    """
    try:
        # 定义格式，支持多种格式
        formats_to_try = [
            "%Y-%m-%d %H:%M",  # 2026-01-20 10:39
            "%Y/%m/%d %H:%M",  # 2026/01/20 10:39
            "%Y-%m-%d %H:%M:%S",  # 2026-01-20 10:39:00
            "%Y-%m-%d",  # 2026-01-20
        ]

        dt = None
        for fmt in formats_to_try:
            try:
                dt = datetime.datetime.strptime(datetime_str, fmt)
                break
            except ValueError:
                continue

        if dt is None:
            raise ValueError(f"无法解析时间字符串: {datetime_str}")

        # 转换为时间戳（秒级），然后转换为毫秒级
        timestamp_seconds = dt.timestamp()
        timestamp_milliseconds = int(timestamp_seconds * 1000)

        return timestamp_milliseconds

    except Exception as e:
        print(f"转换失败: {e}")
        return None