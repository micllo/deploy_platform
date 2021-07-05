# -*- coding:utf-8 -*-
from Env import env_config as cfg
import os, time
from Tools.mongodb import MongodbUtils
from Common.com_func import is_null, log, mongo_exception_send_DD, exception_send_DD, mkdir, deploy_send_DD
from Common.deploy_flow import deployPro
from Tools.date_helper import get_current_iso_date
import re
from bson.objectid import ObjectId
from Tools.decorator_tools import async
import pymongo
from dateutil import parser
# sys.path.append("./")
from Tools.date_helper import get_date_by_days
from fabric.api import *
import traceback

"""
    api 服务底层的业务逻辑
"""

def clear_logs(pro_name, time):
    """
    删除指定时间之前 生成的 日志
      -mmin +1 -> 表示1分钟前的
      -mtime +1 -> 表示1天前的
    :param time:
    :param pro_name:
    :return:
    """
    rm_log_cmd = "find '" + cfg.LOGS_DIR + "' -name '*.log' -mmin +" + str(time) + " -type f -exec rm -rf {} \\;"

    print(rm_log_cmd)
    os.system(rm_log_cmd)


@async
def run_single_deploy(pro_name, deploy_name, exec_type):
    """
    执行单个部署
    :param pro_name
    :param deploy_name：-> ProDemo1-pythonApi-uat-189
    :param exec_type：manual | gitlab
    :return:
    """
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE,
                      collection=pro_name + cfg.TABLE_MODULE) as pro_db:
        try:
            deploy_time = get_current_iso_date()

            # 开启运行状态、初始化进度条、临时更新部署结果
            pro_db.update({"deploy_name": deploy_name}, {"$set": {"run_status": True, "progress": 0,
                                                                  "deploy_result": "部 署 中 ..."}})

            mi = pro_db.find_one({"deploy_name": deploy_name})
            dp = deployPro(pro_name=mi.get("pro_name"), module_name=mi.get("module_name"), deploy_time=str(deploy_time),
                           deploy_name=mi.get("deploy_name"), branch=mi.get("branch"), build_env=mi.get("build_env"),
                           deploy_type=mi.get("deploy_type"), deploy_file=mi.get("deploy_file"),
                           ssh_user=mi.get("ssh_user"), ssh_passwd=mi.get("ssh_passwd"), ssh_host=mi.get("ssh_host"),
                           ssh_port=mi.get("ssh_port"), remote_path=mi.get("remote_path"), exec_type=exec_type,
                           apiTest_status=mi.get("apiTest_status"), apiTest_hostTag=mi.get("apiTest_hostTag"),
                           sonar_status=mi.get("sonar_status"), sonar_key=mi.get("sonar_key"),
                           sonar_name=mi.get("sonar_name"), sonar_version=mi.get("sonar_version"),
                           sonar_sources=mi.get("sonar_sources"), sonar_java_binaries=mi.get("sonar_java_binaries"),
                           jacoco_status=mi.get("jacoco_status"), jacoco_path=mi.get("jacoco_path"))
            # 执行部署
            dp.run_deploy()

            # 关闭运行状态、更新:部署时间、部署结果、部署日志
            pro_db.update({"deploy_name": deploy_name},
                          {"$set": {"run_status": False, "deploy_log": dp.deploy_log,
                                    "deploy_result": dp.deploy_result, "deploy_time": deploy_time}})
        except Exception as e:
            exec_type_name = exec_type == "manual" and "手动执行" or "GitLab执行"
            mongo_exception_send_DD(e=e, msg=exec_type_name + "获取'" + deploy_name + "'部署项目")
        finally:
            # 关闭部署状态
            pro_db.update({"deploy_name": deploy_name}, {"$set": {"run_status": False}})


@async
def update_jacoco_report(pro_name, deploy_name):
    """
    获取最新的测试覆盖率报告
    :return:
    """
    module_name = ""
    ssh_user = ""
    ssh_passwd = ""
    ssh_host = ""
    ssh_port = ""
    remote_path = ""
    deploy_type = ""
    jacoco_path = ""
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name + cfg.TABLE_MODULE) as pro_db:
        try:
            mi = pro_db.find_one({"deploy_name": deploy_name})
            module_name = mi.get("module_name")
            ssh_user = mi.get("ssh_user")
            ssh_passwd = mi.get("ssh_passwd")
            ssh_host = mi.get("ssh_host")
            ssh_port = mi.get("ssh_port")
            remote_path = mi.get("remote_path")
            deploy_type = mi.get("deploy_type")
            jacoco_path = mi.get("jacoco_path")
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="获取'" + deploy_name + "'部署项目最新的测试覆盖率报告")

    try:
        # 本地操作：准备 jacoco_report 下载目录 并清理原有内容
        mkdir(cfg.JACOCO_REPORT_DIR + module_name)  # 若目录不存在 则新增
        with settings(host_string="%s@%s:%s" % (cfg.LOCAL_USER, cfg.LOCAL_HOST, cfg.LOCAL_PORT),
                      password=cfg.LOCAL_PASSWD):
            with cd(cfg.JACOCO_REPORT_DIR + module_name):
                run("rm -rf report")
                run("rm -rf report.tar.gz")

        # 服务端操作：清理原有内容、生成覆盖率报告 并下载到本地
        with settings(host_string="%s@%s:%s" % (ssh_user, ssh_host, ssh_port),
                      password=ssh_passwd):
            with cd(jacoco_path):
                run("rm -rf report")
                run("rm -rf report.tar.gz")
                run("java -jar lib/jacococli.jar dump --address localhost --port 12345 "
                    "--destfile report/jacoco.exec")
                if deploy_type == "War":
                    run("java -jar lib/jacococli.jar report report/jacoco.exec --classfiles " +
                        remote_path + "/webapps/" + module_name + "/WEB-INF/classes --html report")

                run("tar -czvf report.tar.gz report", warn_only=False)
                get(remote_path="report.tar.gz", local_path=cfg.JACOCO_REPORT_DIR + module_name)

        # 本地操作：解压jacoco的report目录
        with settings(host_string="%s@%s:%s" % (cfg.LOCAL_USER, cfg.LOCAL_HOST, cfg.LOCAL_PORT),
                      password=cfg.LOCAL_PASSWD):
            with cd(cfg.JACOCO_REPORT_DIR + module_name):
                run("tar -xzvf report.tar.gz -C .", warn_only=False)
    except Exception as e:
        exception_send_DD(e=e, msg="获取最新测试覆盖率报告")
    else:
        text = "\n\n****" + module_name + " 项目最新的Jacoco测试覆盖率报告：**** [" + cfg.JACOCO_REPORT_BASE_URL + \
               module_name + "/report/index.html](" + cfg.JACOCO_REPORT_BASE_URL + module_name + "/report/index.html)"
        deploy_send_DD(text)


def get_deploy_info(pro_name):
    """
    获取部署信息
    1.区分部署状态：上线的在前面
    2.区分部署顺序：序号小的在前面

    备注：pro_is_run：控制整个pro_name是否存在部署中的模块

    """
    on_line_info = []
    off_line_info = []
    deploy_info_list = []
    run_list = []
    deploy_name_list_str = ""
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name + cfg.TABLE_MODULE) as pro_db:
        try:
            results_cursor = pro_db.find({"pro_name": pro_name})
            for res in results_cursor:
                deploy_module_dict = dict()
                deploy_module_dict["_id"] = str(res.get("_id"))
                deploy_module_dict["serial_num"] = res.get("serial_num")
                deploy_module_dict["deploy_name"] = res.get("deploy_name")
                deploy_module_dict["branch"] = res.get("branch")
                deploy_module_dict["build_env"] = res.get("build_env")
                deploy_module_dict["deploy_status"] = res.get("deploy_status")
                deploy_module_dict["sonar_status"] = res.get("sonar_status")
                deploy_module_dict["jacoco_status"] = res.get("jacoco_status")
                deploy_module_dict["run_status"] = res.get("run_status")
                deploy_module_dict["deploy_result"] = res.get("deploy_result")
                deploy_module_dict["deploy_time"] = res.get("deploy_time")
                deploy_module_dict["progress"] = res.get("progress")
                deploy_name_list_str += res.get("deploy_name") + ","
                if res.get("run_status"):
                    run_list.append(deploy_module_dict)
                if res.get("deploy_status"):
                    on_line_info.append(deploy_module_dict)
                else:
                    off_line_info.append(deploy_module_dict)
            on_line_info = sorted(on_line_info, key=lambda keys: keys['serial_num'])
            deploy_info_list = on_line_info + off_line_info
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="获取'" + pro_name + "'项目部署信息")
        finally:
            module_is_run = len(run_list) != 0
            return deploy_info_list, deploy_name_list_str[:-1], module_is_run


def get_deploy_log(pro_name, deploy_name):
    """ 获取部署日志 """
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name + cfg.TABLE_MODULE) as pro_db:
        try:
            mi = pro_db.find_one({"deploy_name": deploy_name})
            if mi:
                deploy_log_str = mi.get("deploy_log", "暂无部署日志")
                # 将部署日志转成list格式（每行间插入空行）
                deploy_log_str = deploy_log_str.replace("\n\n", "\n-\n")
                deploy_log_list = deploy_log_str.split("\n")
                return deploy_log_list
            else:
                return None
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="获取'" + deploy_name + "'部署项目日志")


def current_run_status(pro_name, deploy_name):
    """
    获取当前运行状态
    :param pro_name:
    :param deploy_name:
    :return:
    """
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name + cfg.TABLE_MODULE) as pro_db:
        try:
            mi = pro_db.find_one({"deploy_name": deploy_name})
            return mi.get("run_status")

        except Exception as e:
            mongo_exception_send_DD(e=e, msg="获取'" + deploy_name + "'项目当前运行状态")


def deploy_is_running(pro_name, deploy_name):
    """
    判断该部署模块是否在运行
    :param pro_name:
    :param deploy_name:
    :return:
    """
    is_run = True
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name + cfg.TABLE_MODULE) as pro_db:
        try:
            deploy_module_cursor = pro_db.find_one({"deploy_name": deploy_name})
            is_run = deploy_module_cursor.get("run_status")
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="获取'" + pro_name + "'项目运行状态列表")
        finally:
            return is_run


def update_deploy_status(pro_name, deploy_name, _id):
    """
    更新模块部署状态（单个）
    :param pro_name:
    :param _id:
    :return:
    """
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name + cfg.TABLE_MODULE) as pro_db:
        try:
            query_dict = {"_id": ObjectId(_id)}
            result = pro_db.find_one(query_dict, {"_id": 0})
            old_deploy_status = result.get("deploy_status")
            new_deploy_status = bool(1 - old_deploy_status)  # 布尔值取反
            update_dict = {"$set": {"deploy_status": new_deploy_status}}
            pro_db.update_one(query_dict, update_dict)
            return new_deploy_status
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="更新'" + deploy_name + "'模块部署状态(单个)")
            return "mongo error"


def get_module_info_by_id(request_args, pro_name):
    """
    通过id获取部署模块信息（填充编辑弹层）
    :return:
    """
    _id = request_args.get("_id", "").strip()
    query_dict = {"_id": ObjectId(_id)}
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name + cfg.TABLE_MODULE) as pro_db:
        try:
            deploy_module_dict = pro_db.find_one(query_dict)
        except Exception as e:
            mongo_exception_send_DD(e=e, msg="通过id获取'" + pro_name + "'项目部署模块信息")
            return "mongo error"

    # 将所有字段转换成 string 类型
    for field, value in deploy_module_dict.items():
        # 若"部署序号"为0，则赋空值 传递给编辑弹层显示
        if field in ["serial_num", "progress"]:
            deploy_module_dict[field] = value != 0 and str(value) or ""

        if field in ["_id", "run_status", "deploy_status", "sonar_status",
                     "jacoco_status", "apiTest_status", "deploy_time"]:
            deploy_module_dict[field] = str(value)

    return deploy_module_dict


def update_deploy_info(request_json, pro_name):
    """
    更新 部署信息
    :param request_json:
    :param pro_name:
    :return:

        注意：部署序号不能相同
    """
    # 获取请求中的参数
    _id = request_json.get("_id", "").strip()
    build_env = request_json.get("build_env", "").strip()
    serial_num_str = request_json.get("serial_num", "").strip()
    branch = request_json.get("branch", "").strip()
    sonar_status = request_json.get("sonar_status", "").strip()
    apiTest_status = request_json.get("apiTest_status", "").strip()
    apiTest_hostTag = request_json.get("apiTest_hostTag", "").strip()
    sonar_status = sonar_status == "True" or False
    apiTest_status = apiTest_status == "True" or False

    if is_null(build_env) or is_null(serial_num_str) or is_null(branch):
        return "必填项 不能为空"

    update_dict = {"build_env": build_env, "serial_num": int(serial_num_str), "branch": branch,
                   "sonar_status": sonar_status, "apiTest_status": apiTest_status, "apiTest_hostTag": apiTest_hostTag}

    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name + cfg.TABLE_MODULE) as pro_db:
        try:
            # 验证数据库中是否已存在需要修改的部署序号
            old_info_dict = pro_db.find_one({"_id": ObjectId(_id)})
            old_serial_num = old_info_dict.get("serial_num")
            if int(serial_num_str) != old_serial_num:
                serial_num_same_module = pro_db.find_one({"serial_num": int(serial_num_str)})
                if serial_num_same_module:
                    return "部署序号 已存在 ！"
            # 更新
            pro_db.update({"_id": ObjectId(_id)}, {"$set": update_dict})
        except Exception as e:
            log.error(e)
            mongo_exception_send_DD(e=e, msg="为'" + pro_name + "'项目'更新部署信息")
            return "mongo error"
    return "更新成功 ！"


def get_moudule_current_progress(pro_name, deploy_name):
    """
        获取模块当前进度
    """
    with MongodbUtils(ip=cfg.MONGODB_ADDR, database=cfg.MONGODB_DATABASE, collection=pro_name + cfg.TABLE_MODULE) as pro_db:
        try:
            deploy_name_res = pro_db.find_one({"deploy_name": deploy_name})
        except Exception as e:
            log.error(e)
            mongo_exception_send_DD(e=e, msg="获取'" + deploy_name + "'模块'当前进度")
            return "mongo error"
        return str(deploy_name_res.get("_id")), deploy_name_res.get("run_status"), deploy_name_res.get("progress")


if __name__ == "__main__":
    print(get_deploy_log("pro_demo_1", "pro_demo_1-deploy-uat-9"))
    # print(get_deploy_log("pro_demo_1", "pro_demo_1-pythonApi-uat-198"))




