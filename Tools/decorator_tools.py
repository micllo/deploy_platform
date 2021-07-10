# -*- coding: utf-8 -*-
"""
装饰器
"""
import time
from Tools.log import FrameLog
from Tools.date_helper import current_timestamp
from threading import Thread
import threading
from functools import wraps

save_mutex = threading.Lock()
log = FrameLog().log()


def retry_request(try_limit=3, interval_time=1, log_show=True):
    """
    接口重试
    :param try_limit:
    :param interval_time:
    :param log_show:
    :return:

     备注：若重试全部失败后，返回 31500
    """
    def try_func(func):
        def wrapper(*args, **kwargs):
            try_cnt = 0
            while try_cnt < try_limit:
                try:
                    st = time.time()
                    res = func(*args, **kwargs)
                    et = time.time()
                    if log_show:
                        log.info("%s: DONE %s" % (func.__name__, (et-st)))
                    return res
                except Exception as e:
                    time.sleep(interval_time)
                    try_cnt += 1
                    if log_show:
                        log.error(e)
                        log.warning("%s: RETRY CNT %s" % (func.__name__, try_cnt))
            if log_show:
                log.warning("%s: FAILED" % func.__name__)
            return 31500
        return wrapper
    return try_func


def async(func, is_join=False):
    """
    异步开线程调用
    :param func: 被修饰的函数
    :param is_join: 是否线程等待
    :return:
    """
    def wrapper(*args, **kwargs):
        thr = Thread(target=func, args=args, kwargs=kwargs)
        thr.start()
        if is_join:
            thr.join()
    return wrapper


def elapse_time(func):
    """
    计算方法耗时
    :param func: 被修饰的函数
    :return:
    """
    def wrapper(*args, **kwargs):
        st = current_timestamp()
        res = func(*args, **kwargs)
        et = current_timestamp()
        log.info("%s ELAPSE TIME: %s" % (func.__name__, (et-st)/1000.0))
        return res
    return wrapper


def thread_save(func):
    @wraps(func)
    def processed_res(*args, **kwargs):
        save_mutex.acquire()
        st = time.time()
        res = func(*args, **kwargs)
        et = time.time()
        save_mutex.release()
        log.info(u"%s: DONE %s" % (func.__name__, (et-st)))
        return res
    return processed_res