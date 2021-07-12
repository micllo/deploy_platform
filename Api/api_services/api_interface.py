# -*- coding: utf-8 -*-
from Api import *
from flask import render_template, request
import json
from Config.error_mapping import *
from Api.api_services.api_template import interface_template
from Api.api_services.api_calculate import *
from Common.com_func import is_null
from Env import env_config as cfg
from Config.pro_config import pro_name_list

"""
api 服务接口
"""


# http://127.0.0.1:3310/api_local/DEPLOY/index
@flask_app.route("/DEPLOY/index", methods=["GET"])
def show_index():
    """   显示 首页   """
    result_dict = dict()
    result_dict["nginx_api_proxy"] = cfg.NGINX_API_PROXY
    result_dict["api_addr"] = cfg.API_ADDR
    result_dict["pro_name_list"] = pro_name_list
    result_dict["pro_num"] = len(pro_name_list)
    return render_template('index.html', tasks=result_dict)


# http://127.0.0.1:3310/api_local/DEPLOY/show_deploy_info/pro_demo_1
@flask_app.route("/DEPLOY/show_deploy_info/<pro_name>", methods=["GET"])
def show_deploy_info(pro_name):
    """   显示 部署页面   """
    res = dict()
    res["nginx_api_proxy"] = cfg.NGINX_API_PROXY
    res["pro_name"] = pro_name
    res["batch_deploy_status"] = get_batch_deploy_status(pro_name=pro_name)
    res["progress"], res["done_num"], res["all_num"], res["running_serial_num"] = \
        get_batch_current_progress(pro_name=pro_name)
    res["deploy_info_list"], res["deploy_name_list_str"], res["module_is_run"] = get_deploy_info(pro_name)
    res["sonar_url"] = cfg.SONAR_URL
    res["jacoco_report_url"] = cfg.JACOCO_REPORT_BASE_URL
    res["apiTest_report_url"] = cfg.API_TEST_REPORT_URL
    return render_template('deploy.html', tasks=res)


# http://127.0.0.1:3310/api_local/DEPLOY/show_deploy_log
@flask_app.route("/DEPLOY/show_deploy_log/<pro_name>", methods=["GET"])
def show_deploy_log(pro_name):
    """   显示 部署日志   """
    result_dict = dict()
    result_dict["nginx_api_proxy"] = cfg.NGINX_API_PROXY
    result_dict["pro_name"] = pro_name
    return render_template('log.html', tasks=result_dict)


# http://192.168.31.9:3310/api_local/DEPLOY/single_deploy/manual/pro_demo_1/pro_demo_1-pythonApi-uat-198
# http://192.168.31.9:3310/api_local/DEPLOY/single_deploy/manual/pro_demo_1/pro_demo_1-deploy-uat-9
@flask_app.route("/DEPLOY/single_deploy/<exec_type>/<pro_name>/<deploy_name>", methods=["POST"])
def single_deploy(exec_type, pro_name, deploy_name):
    """
    单个部署
        deploy_name： pro_demo_1-pythonApi-uat-198
        exec_type：   manual | batch | gitlab
    :return:
    """
    res_info = dict()
    batch_deploy_status = get_batch_deploy_status(pro_name=pro_name)
    run_status, gitlab_status = get_current_status(pro_name, deploy_name)
    if batch_deploy_status:
        msg = pro_name + " 项目批量部署正在进行中，请稍后再执行部署！"
        res_info["msg"] = msg
        deploy_send_DD("#### " + msg)
    else:
        if run_status:
            msg = deploy_name + " 模块当前正在部署中，请稍后再执行部署！"
            if exec_type == "gitlab":
                deploy_send_DD("#### " + msg)
            res_info["msg"] = msg
        else:
            if exec_type == "gitlab" and not gitlab_status:
                res_info["msg"] = deploy_name + "模块的 'GitLab'部署状态已关闭"
            else:
                # 在线程中进行部署
                async_exec(target=run_single_deploy, args=(pro_name, deploy_name, exec_type))
                res_info["msg"] = deploy_name + "部署开始，请关注钉钉通知"
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/DEPLOY/batch_deploy/<pro_name>", methods=["POST"])
def batch_deploy(pro_name):
    """
    批量部署
    :return:
    """
    res_info = dict()
    if pro_is_running(pro_name):
        res_info["msg"] = pro_name + " 项目存在部署中的模块"
    else:
        deploy_list = get_batch_deploy_list(pro_name=pro_name)
        if is_null(deploy_list):
            res_info["msg"] = pro_name + " 项目没有上线的部署模块"
        else:
            run_batch_deploy_async(pro_name=pro_name, deploy_list=deploy_list)
            res_info["msg"] = pro_name + " 项目批量部署进行中，请关注钉钉通知"
    return json.dumps(res_info, ensure_ascii=False)


# http://127.0.0.1:3310/api_local/DEPLOY/get_jacoco_report/pro_demo_1/pro_demo_1-deploy-uat-9
@flask_app.route("/DEPLOY/get_jacoco_report/<pro_name>/<deploy_name>", methods=["GET"])
def get_jacoco_report(pro_name, deploy_name):
    """
    获取最新的测试覆盖率报告
    :param pro_name
    :param deploy_name：-> pro_demo_1-pythonApi-uat-198
    :return:
    """
    res_info = dict()
    update_jacoco_report(pro_name, deploy_name)
    res_info["msg"] = "测试覆盖率报告更新中，请关注钉钉通知"
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/DEPLOY/set_deploy_status/<pro_name>/<deploy_name>/<_id>", methods=["GET"])
def set_deploy_status(pro_name, deploy_name, _id):
    """
    设置某个'部署模块'的'状态'(上下线)
    :param pro_name:
    :param deploy_name:
    :param _id:
    :return:
    """
    new_deploy_status = None
    if is_null(pro_name) or is_null(_id):
        msg = PARAMS_NOT_NONE
    elif deploy_is_running(pro_name, deploy_name):
        msg = CURRENT_IS_RUNNING
    else:
        new_deploy_status = update_deploy_status(pro_name, deploy_name, _id)
        msg = new_deploy_status == "mongo error" and MONGO_CONNECT_FAIL or UPDATE_SUCCESS
    re_dict = interface_template(msg, {"pro_name": pro_name, "_id": _id, "new_deploy_status": new_deploy_status})
    return json.dumps(re_dict, ensure_ascii=False)


@flask_app.route("/DEPLOY/get_module_info/<pro_name>", methods=["GET"])
def get_module_info(pro_name):
    """
    通过id获取部署模块信息（填充编辑弹层）
    :param pro_name
    :return:
    """
    res_info = dict()
    res_info["deploy_module_dict"] = get_module_info_by_id(request_args=request.args, pro_name=pro_name)
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/DEPLOY/edit_deploy_info/<pro_name>", methods=["POST"])
def edit_deploy_info(pro_name):
    """
    编辑 部署信息
    :param pro_name
    :return:
    """
    res_info = dict()
    res_info["msg"] = update_deploy_info(request_json=request.json, pro_name=pro_name)
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/DEPLOY/search_deploy_log", methods=["GET"])
def search_deploy_log():
    """
    获取 部署日志
    :return:
    """
    pro_name = request.args.get("pro_name", "").strip()
    deploy_name = request.args.get("deploy_name", "").strip()
    res_info = dict()
    res_info["deploy_log_list"] = get_deploy_log(pro_name, deploy_name)
    if res_info["deploy_log_list"]:
        res_info["msg"] = "查询成功"
    else:
        res_info["msg"] = "部署名称不存在"
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/DEPLOY/get_module_progress/<pro_name>/<deploy_name>", methods=["GET"])
def get_module_progress(pro_name, deploy_name):
    """
    获取 正在运行中的模块 当前进度
    :param pro_name
    :param deploy_name
    :return:
    """
    res_info = dict()
    res_info["_id"], res_info["run_status"], res_info["progress"] \
        = get_module_current_progress(pro_name=pro_name, deploy_name=deploy_name)
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/DEPLOY/get_batch_progress/<pro_name>", methods=["GET"])
def get_batch_progress(pro_name):
    """
    获取 批量部署 当前进度
    :param pro_name
    :return:
    """
    res = dict()
    res["progress"], res["done_num"], res["all_num"], res['running_serial_num'] = get_batch_current_progress(pro_name=pro_name)
    return json.dumps(res, ensure_ascii=False)


@flask_app.route("/DEPLOY/set_deploy_status_all/<pro_name>/<deploy_status>", methods=["GET"])
def set_case_status_all(pro_name, deploy_status):
    """
    设置整个项目'部署模块'的'状态'(上下线)
    :param pro_name:
    :param deploy_status:
    :return:
    """
    res_info = dict()
    if is_null(pro_name) or is_null(deploy_status):
        res_info["msg"] = PARAMS_NOT_NONE
    elif pro_is_running(pro_name):
        res_info["msg"] = CURRENT_IS_RUNNING
    else:
        if deploy_status in [True, False, "false", "FALSE", "TRUE", "true"]:
            deploy_status = deploy_status in [True, "TRUE", "true"] and True or False
            res_info["msg"] = update_case_status_all(pro_name, deploy_status)
        else:
            res_info["msg"] = REQUEST_ARGS_WRONG
    return json.dumps(res_info, ensure_ascii=False)


@flask_app.route("/DEPLOY/stop_run_status_all/<pro_name>", methods=["GET"])
def stop_run_status_all(pro_name):
    """
    停止项目所有'模块'的'运行状态'
    :param pro_name:
    :return:
    """
    res_info = dict()
    if is_null(pro_name):
        res_info["msg"] = PARAMS_NOT_NONE
    else:
        res_info["msg"] = stop_run_status(pro_name)
    return json.dumps(res_info, ensure_ascii=False)

