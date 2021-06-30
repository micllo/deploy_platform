# -*- coding:utf-8 -*-
import os
import threading
from Tools.log import FrameLog
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import traceback
from Env import env_config as cfg
import json
import re
import requests


log = FrameLog().log()

NULL_LIST = [" ", "", None, "nan", "NaN", "None", "null", []]


def is_null(tgt):
    """
    查看输入的是不是null
    :param tgt: 输入的string或者unicode
    :return: boolean
    """
    if tgt not in NULL_LIST:
        isnull_res = False
    else:
        isnull_res = True

    return isnull_res


# 多线程重载 run 方法
class MyThread(threading.Thread):

    def __init__(self, func, driver, test_class_list):
        super(MyThread, self).__init__()
        # threading.Thread.__init__(self)
        self.func = func
        self.driver = driver
        self.test_class_list = test_class_list

    def run(self):
        print("Starting " + self.name)
        print("Exiting " + self.name)
        self.func(self.driver, self.test_class_list)


# 获取项目路径
def project_path():
    return os.path.split(os.path.realpath(__file__))[0].split('Common')[0]


# 递归创建目录
def mkdir(path):
    path = path.strip()  # 去除首位空格
    path = path.rstrip("//")  # 去除尾部 / 符号
    is_exists = os.path.exists(path)  # 判断路径是否存在(True存在，False不存在)
    # 判断结果
    if not is_exists:
        os.makedirs(path)
        log.info(path + ' 目录创建成功')
        return True
    else:
        log.info(path + ' 目录已存在')
        return False


def send_mail(subject, content, to_list, attach_file=None):
    """
    [ 发送邮件 ]
    :param subject: 邮件主题
    :param content: 邮件内容
    :param to_list: 邮件发送者列表
    :param attach_file: 附件
    :return:
    """
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = cfg.ERROR_MAIL_ACCOUNT
    msg['To'] = ";".join(to_list)
    msg.attach(MIMEText(content, _subtype='plain', _charset='utf-8'))
    if not is_null(attach_file):
        attach = MIMEText(open(attach_file, 'rb').read(), 'base64', 'utf-8')
        # 指定当前文件格式类型
        attach['Content-type'] = 'application/octet-stream'
        # 配置附件显示的文件名称,当点击下载附件时，默认使用的保存文件的名称
        attach['Content-Disposition'] = "attachment;filename=" + attach_file.split("/")[-1]
        # 把附件添加到msg中
        msg.attach(attach)
    try:
        server = smtplib.SMTP()
        server.connect(host=cfg.ERROR_MAIL_HOST, port=25)
        server.login(cfg.ERROR_MAIL_ACCOUNT, cfg.ERROR_MAIL_PASSWD)
        server.sendmail(cfg.ERROR_MAIL_ACCOUNT, to_list, msg.as_string())
        server.close()
        log.info("邮件发送成功！")
    except Exception as e:
        print(str(e))
        print(traceback.format_exc())
        log.error("邮件发送失败！")


def send_DD(dd_group_id, title, text, at_phones="", is_at_all=False):
    """
    发 送 钉 钉
    :param dd_group_id: 发送的钉钉消息群
    :param title: 消息title
    :param text:  消息内容
    :param at_phones: 需要@的手机号
    :param is_at_all: 是否@所有人
    :return:
      备注：若要@某个人，则需要在'text'中@其手机号
           at_text -> \n\n@138xxxxxx @139xxxxxx
      注意：
         钉钉机器人设置了关键字过滤
         title 或 text 中必须包含 "监控" 两字
    """
    at_all = "true"
    at_mobiles = []
    at_text = ""
    if not is_at_all:
        at_all = "false"
        at_mobiles = at_phones.split(",")
        at_text += "\n\n"
        at_mobile_text = ""
        for mobile in at_mobiles:
            at_mobile_text += "@" + mobile + " "
        at_text += at_mobile_text
    data = {"msgtype": "markdown"}
    data["markdown"] = {"title": "[API监控] " + title, "text": text + at_text}
    data["at"] = {"atMobiles": at_mobiles, "isAtAll": at_all}
    dd_url = "https://oapi.dingtalk.com/robot/send?access_token=" + dd_group_id
    log.info(data)
    headers = {'Content-Type': 'application/json'}
    try:
        requests.post(url=dd_url, data=json.dumps(data), headers=headers)
        log.info("钉钉发送成功")
    except Exception as e:
        log.error("钉钉发送失败")
        log.error(e)


def mongo_exception_send_DD(e, msg):
    """
    发现异常时钉钉通知
    :param e:
    :param msg:
    :return:
    """
    title = "'mongo'操作通知"
    text = "#### [DEPLOY]部署'mongo'操作错误\n\n****操作方式：" + msg + "****\n\n****错误原因：" + str(e) + "****"
    send_DD(dd_group_id=cfg.DD_MONITOR_GROUP, title=title, text=text, at_phones=cfg.DD_AT_FXC, is_at_all=False)


def exception_send_DD(e, msg):
    """
    发现异常时钉钉通知
    :param e:
    :param msg:
    :return:
    """
    title = "'异常'操作通知"
    text = "#### [DEPLOY]'异常'操作错误\n\n****操作方式：" + msg + "****\n\n****错误原因：" + str(e) + "****"
    send_DD(dd_group_id=cfg.DD_MONITOR_GROUP, title=title, text=text, at_phones=cfg.DD_AT_FXC, is_at_all=False)


def deploy_monitor_send_DD(deploy_name, module_name, exec_type, deploy_host, branch, build_env, deploy_result,
                           deploy_time, sonar_status, sonar_key, jacoco_status):
    """
    部署监控 发钉钉
    :param deploy_name: ProDemo1-pythonApi-uat-189
    :param exec_type:   manual | gitlab
    :param deploy_host:
    :param branch:
    :param build_env:
    :param deploy_result:
    :param deploy_time:
    :param sonar_status:
    :param sonar_key:
    :param module_name:
    :param jacoco_status:
    :return:
    "\n\n****报告地址：**** [http://" + \
           cfg.TEST_REPORT_URL + pro_name + "](http://" + cfg.TEST_REPORT_URL + pro_name + ")"
    """
    exec_type_name = exec_type == "manual" and "手动执行" or "GitLab执行"
    text = "#### ****部署项目：**** " + deploy_name + "\n\n****部署服务：**** " + deploy_host + \
           "\n\n****部署分支：**** " + branch + "\n\n****构建环境：**** " + build_env + \
           "\n\n****部署方式：**** " + exec_type_name + "\n\n****部署时间：**** " + deploy_time + "\n\n****部署结果：**** "
    if "成功" in deploy_result:
        text += deploy_result
        if sonar_status and "Sonar" not in deploy_result:
            text += "\n\n****Sonar报告：**** [" + cfg.SONAR_URL + sonar_key + "](" + cfg.SONAR_URL + sonar_key + ")"
        if jacoco_status:
            text += "\n\n****Jacoco报告：**** [" + cfg.JACOCO_REPORT_BASE_URL + module_name + "/report/index.html](" + \
                    cfg.JACOCO_REPORT_BASE_URL + module_name + "/report/index.html)"
        send_DD(dd_group_id=cfg.DD_MONITOR_GROUP, title="部署结果", text=text, at_phones=cfg.DD_AT_FXC, is_at_all=False)
    else:
        text += "部署失败 ( " + deploy_result + " )"
        send_DD(dd_group_id=cfg.DD_MONITOR_GROUP, title="部署结果", text=text, is_at_all=True)


# def update_jacoco_send_DD(module_name):
#     """ 更新测试覆盖率统计报告 """
#     text = "\n\n****" + module_name + " 项目最新的Jacoco测试覆盖率报告：**** [" + cfg.JACOCO_REPORT_BASE_URL + module_name + \
#            "/report/index.html](" + cfg.JACOCO_REPORT_BASE_URL + module_name + "/report/index.html)"
#     send_DD(dd_group_id=cfg.DD_MONITOR_GROUP, title="部署结果", text=text, is_at_all=True)


def deploy_send_DD(text):
    """ 部署后 通知钉钉 """
    send_DD(dd_group_id=cfg.DD_MONITOR_GROUP, title="部署结果", text=text, is_at_all=True)


if __name__ == "__main__":
    pass
    # attach_file = cfg.REPORTS_DIR + "report.html"
    # send_mail(subject="测试发送", content="测试内容。。。。", to_list=cfg.MAIL_LIST, attach_file=attach_file)

    # print("项目路径：" + project_path())
    # print("被测系统URL：" + get_config_ini("test_url", "ctrip_url"))
    # print()
    # print(os.path.split(os.path.realpath(__file__)))
    # print(os.path.split(os.path.realpath(__file__))[0])
    # print(os.path.split(os.path.realpath(__file__))[0].split('C'))
    # print(os.path.split(os.path.realpath(__file__))[0].split('C')[0])





