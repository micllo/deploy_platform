# coding:UTF-8
import pymongo
from Env import env_config as cfg

"""
    【 Docker 项 目 配 置 】
    1.在 Docker 中启动新项目时，需要创建 xxxx_config 数据库
    2.为该数据库添加 添加 批量部署状态
        {"batch_deploy_status": False}
"""


def create_collection(pro_name):

    # 创建mongo连接
    myclient = pymongo.MongoClient("mongodb://" + cfg.MONGODB_ADDR + "/")

    # 连接 数据库
    mydb = myclient[cfg.MONGODB_DATABASE]

    # 获取 集合（若不存在）
    mycoll = mydb[pro_name + "_config"]

    # 判断 是否存在 'batch_deploy_status' 记录
    results_cursor = mycoll.find()
    for res in results_cursor:
        if res.get("batch_deploy_status") is not None:
            break
    else:
        mycoll.insert_one({"batch_deploy_status": False})
        print(pro_name + "_config 表 新增 batch_deploy_status 记录成功！")


if __name__ == '__main__':

    create_collection("pro_demo_1")
