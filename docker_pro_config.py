# coding:UTF-8
import pymongo
# from Env import env_config as cfg
from Env import env_config_docker as cfg

"""
    【 Docker 项 目 配 置 】
    1.在 Docker 中启动新项目时，需要创建 xxxx_config 数据库
    2.为该项目添加 批量部署状态
       {"config_type":"status", "config_name":"batch_deploy", "config_value": False}
"""


def create_collection(pro_name):

    # 创建mongo连接
    myclient = pymongo.MongoClient("mongodb://" + cfg.MONGODB_ADDR + "/")

    # 连接 数据库
    mydb = myclient[cfg.MONGODB_DATABASE]

    # 获取 集合（若不存在）
    mycoll = mydb[pro_name + "_config"]

    # 清空集合
    # mycoll.remove()

    # 判断 config_name = batch_deploy 是否存在
    res = mycoll.find_one({"config_name": "batch_deploy"})
    if res:
        print(pro_name + "_config 表 存在 config_name = batch_deploy 记录")
    else:
        mycoll.insert_one({"config_type": "status", "config_name": "batch_deploy", "config_value": False})
        print(pro_name + "_config 表 新增 config_name = batch_deploy 记录成功！")


if __name__ == '__main__':

    create_collection("pro_demo_1")
