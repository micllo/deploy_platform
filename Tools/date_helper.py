# -*- coding: utf-8 -*-
"""
时间日期的转化文件
"""
import time
import datetime
from datetime import timedelta
from dateutil import parser
import calendar;


def get_current_timestamp():
    """
    获取当前时间戳
    :return:
    """
    return calendar.timegm(time.gmtime())

def get_date_by_days(days=1, time_type="%Y-%m-%dT H:%M:%S"):
    """
    获取 多少天 之前 的日期
    :param days:
    :param time_type:
    :return:
    """
    # 格式化为 年 月 日
    # return (datetime.date.today() - timedelta(days=days)).strftime(time_type)
    # 格式化为 年 月 日 时 分 秒
    return (datetime.datetime.now() - timedelta(days=days)).strftime(time_type)


def get_current_iso_date():
    now_str = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time()))
    ISODate = parser.parse(now_str)
    return ISODate


# @return: 当前的datetime时间戳
def now_dt():
    return datetime.datetime.now()


# 当前时间
def current_date():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def current_day():
    return datetime.datetime.now().strftime('%Y-%m-%d')


def current_mth():
    return datetime.datetime.now().strftime('%Y-%m')


def current_timestamp():
    current_timestamp_var = int(time.time()*1000)

    return current_timestamp_var


# @return: 当前的date
def now_date():
    return datetime.datetime.now().date()


# @return: 返回1970.01.01，datetime类型
def null_dt():
    return datetime.datetime(1970, 1, 1)


# @return: 返回1970.01.01，date类型
def null_date():
    return datetime.date(1970, 1, 1)


# @param: 输入日期格式，
# @return: datetime类型
def get_dt(dt_str="1970-01-01 00:00:00", dt_format='%Y-%m-%d %H:%M:%S'):
    return datetime.datetime.strptime(dt_str, dt_format)


# @param: 输入日期格式，
# @return: date类型
def get_date(date_str="1970-01-01", dt_format='%Y-%m-%d'):
    return get_dt(date_str, dt_format).date()


def get_dt_day(dt, dt_format='%Y-%m-%d'):
    return dt.strftime(dt_format)


# @param: datetime
# @return: string类型
def get_dt_mth(dt, dt_format='%Y-%m'):
    return dt.strftime(dt_format)


# @param: datetime
# @return: string类型
def get_dt_str(dt, dt_format="%Y-%m-%d %H:%M:%S"):
    return dt.strftime(dt_format)


def timestamp_tran_date_str(timestamp):
    """
    时间戳转化成字符型日期格式
    :return: 字符型日期格式
    """
    return time.strftime('%Y-%m-%d', time.localtime(timestamp/1000))


def date_str_tran(date_str):
    """
    将字符串格式时间转成 timestamp 13位格式
    :param date_str: 需要转换的时间
    :return: datetime
    """
    try:
        date_tuple = time.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        timestamp = int(time.mktime(date_tuple)*1000)
    except Exception as e:
        print(e)
        timestamp = None
    return timestamp


def timestamp_str_tran(timestamp):
    """
    将字符串格式的时间戳 转成 日期格式
    :param timestamp:
    :return:
    """
    if timestamp:
        try:
            time_array = time.localtime(int(timestamp) / 1000)
            date = time.strftime("%Y-%m-%d %H:%M:%S", time_array)
        except Exception as e:
            print(e)
    else:
        date = "None"
    return date


if __name__ == "__main__":

    # 获取当前时间戳
    time_stamp = time.time()
    print(time_stamp)

    # 时间戳 --> 时间元祖
    time_tuple = time.localtime(time_stamp)
    print(time_tuple)

    # 时间元祖 --> 时间戳
    time_stamp2 = time.mktime(time_tuple)
    print(time_stamp2)

    # 时间元祖 --> 时间字符串
    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time_tuple)
    print(time_str)

    # 时间字符串 --> 时间元祖
    time_tuple2 = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    print(time_tuple2)

