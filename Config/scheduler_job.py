# -*- coding:utf-8 -*-

class Config(object):

    # 监听出错的任务
    @staticmethod
    def my_listener(event):
        if event.exception:
            print('任务出错了！！！！！！')
        else:
            print('任务照常运行......')

    JOBS = [
        {
            'id': 'job_test1',     # 任务的唯一id
            'func': 'Config.scheduler_job:job_test',  # 执行任务的方法名(包路径.模块名:方法名)
            'args': (1, 2),      # 任务参数
            'trigger': 'cron',  # cron、interval、date
            'day_of_week': '1-6',  # 周日 0
            'hour': 10,
            'minute': '30-31',
            'second': "*/10"
            # 执行时间段：周一到周六，10点30-31分之间，每隔10秒 执行一次
        }
        # {
        #     'id': 'clear_logs',
        #     'func': 'Api.api_services.api_calculate:clear_logs',
        #     'args': [7],
        #     'trigger': 'interval',
        #     'seconds': 60
        #     # 测试使用
        #     # 每周日10点30分10秒 -> 清理7天前的报告和日志（注意：正式使用时 要把 '-mmin' 改成 '-mtime'）
        # }
    ]

    # JOBS = [
    #     {
    #         'id': 'clear_logs',
    #         'func': 'Api.api_services.api_calculate:clear_logs',
    #         'args': [7],
    #         'trigger': 'cron',
    #         'day_of_week': '0',
    #         'hour': 10,
    #         'minute': '30',
    #         'second': "10"
    #         # 清除 excel 和 日志
    #         # 每周日10点30分10秒 -> 清理7天前的报告和日志（注意：正式使用时 要把 '-mmin' 改成 '-mtime'）
    #     }
    # ]


def job_test(a, b):
    print(str(a) + ' ' + str(b))
