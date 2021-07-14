# -*- coding:utf-8 -*-

# 日志、报告 等路径
PRO_PATH = "/Users/micllo/Documents/works/GitHub/deploy_platform/"
LOGS_DIR = PRO_PATH + "Logs/"
REPORTS_DIR = PRO_PATH + "Reports/"
JACOCO_REPORT_DIR = PRO_PATH + "Jacoco_Report/"

# 服务器地址
SERVER_IP = "127.0.0.1"

# Nginx 端口
NGINX_PORT = "3310"

# Nginx中的接口反向代理名称
NGINX_API_PROXY = "api_local"

# Mongo 地址
MONGODB_ADDR = SERVER_IP + ":27017"

# 本地环境
LOCAL_USER = "micllo"
LOCAL_PASSWD = "abc123"
LOCAL_HOST = SERVER_IP
LOCAL_PORT = "22"
WORKSPACE = PRO_PATH + "workspace/"

# API 接口测试
API_TEST_BASE_URL = "http://192.168.31.9:7060/api_local/API"
API_TEST_URL = API_TEST_BASE_URL + "/exec/deploy"
API_TEST_REPORT_URL = API_TEST_BASE_URL + "/get_test_report/"

# Sonar报告 地址
SONAR_URL = "http://" + SERVER_IP + ":9000/dashboard?id="

# Jacoco测试覆盖率报告目录
# http://127.0.0.1:3310/jacoco_report_local/deploy/report/index.html
JACOCO_REPORT_BASE_URL = "http://" + SERVER_IP + ":" + NGINX_PORT + "/jacoco_report_local/"

# 当前环境
CURRENT_ENV = "MAC"

############################################# 相 同 的 配 置 #############################################


# 接口地址( uwsgi )
API_ADDR = SERVER_IP + ":" + NGINX_PORT + "/" + NGINX_API_PROXY

# mongo 数据库
MONGODB_DATABASE = "deploy_platform"
TABLE_MODULE = "_module"
TABLE_CONFIG = "_config"

# gitlab 下载地址
GITLAB_USERNAME = "root"
GITLAB_PASSWD = "abcABC123"
GITLAB_IP = "192.168.31.198"
GITLAB_PORT = "8088"
GITLAB_BASE_URL = "http://" + GITLAB_USERNAME + ":" + GITLAB_PASSWD + "@" + GITLAB_IP + ":" + GITLAB_PORT + "/root/"

# 构建的时候使用前端静态文件路径 ( Api/__init__.py文件的同级目录 ) 'static'、'templates'
GULP_STATIC_PATH = '../Build'
GULP_TEMPLATE_PATH = '../Build/templates'

# 邮箱配置参数(发送者)
ERROR_MAIL_HOST = "smtp.163.com"
ERROR_MAIL_ACCOUNT = "miclloo@163.com"
ERROR_MAIL_PASSWD = "qweasd123"  # 客户端授权密码，非登录密码

# 报错邮箱地址(接收者)
MAIL_LIST = ["micllo@126.com"]

# 钉钉通知群
DD_MONITOR_GROUP = "3a2069108f0775762cbbfea363984c9bf59fce5967ada82c78c9fb8df354a624"
DD_AT_PHONES = "13816439135,18717854213"
DD_AT_FXC = "13816439135"
