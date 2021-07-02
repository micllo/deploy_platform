from Env import env_config as cfg
import pymongo


def pro_demo_1_uat():
    """
    部署模块导入数据库
    < 备 注 >
    1.remote_path 远程路径 在服务器端 需要手动 创建 tmp 临时目录
    2.deploy_status：部署状态（控制部署上下线状态）
    3.sonar_status：静态扫描状态（判断是否需要执行sonar）
    4.jacoco_status：测试覆盖率统计（只有java项目才需要）
    5.run_status：运行状态（判断当前项目是否存在运行中的模块）
    """
    pro_name = "pro_demo_1"
    myclient = pymongo.MongoClient("mongodb://" + cfg.MONGODB_ADDR + "/")  # 创建mongo连接
    mydb = myclient[cfg.MONGODB_DATABASE]  # 连接 数据库
    mycoll = mydb[pro_name + cfg.TABLE_MODULE]  # 获取 集合（若不存在，则创建）
    mycoll.remove()  # 清空集合

    module_info_list = []
    proDemo1_pythonApi_uat_198 = {
        "run_status": True,
        "serial_num": 2,
        "pro_name": "pro_demo_1",
        "module_name": "pythonApi",
        "deploy_name": "pro_demo_1-pythonApi-uat-198",
        "branch": "develop",
        "build_env": "uat",
        "deploy_type": "Python",
        "deploy_file": "pythonApi.tar.gz",
        "ssh_host": "192.168.31.198",
        "ssh_port": "1122",
        "ssh_user": "centos",
        "ssh_passwd": "centos",
        "remote_path": "/opt/project",
        "deploy_status": False,
        "deploy_time": "----",
        "deploy_log": "----",
        "deploy_result": "----",
        "apiTest_status": False,
        "apiTest_hostTag": "",
        "sonar_status": False,
        "sonar_key": "pythonApi",
        "sonar_name": "pythonApi",
        "sonar_version": "1.0",
        "sonar_sources": ".",
        "sonar_java_binaries": "",
        "jacoco_status": False,
        "jacoco_path": "",
        "progress": 0
    }
    module_info_list.append(proDemo1_pythonApi_uat_198)

    proDemo1_deploy_uat_9 = {
        "run_status": False,
        "serial_num": 1,
        "pro_name": "pro_demo_1",
        "module_name": "deploy",
        "deploy_name": "pro_demo_1-deploy-uat-9",
        "branch": "develop",
        "build_env": "uat",
        "deploy_type": "War",
        "deploy_file": "deploy.war",
        "ssh_host": "192.168.31.9",
        "ssh_port": "22",
        "ssh_user": "micllo",
        "ssh_passwd": "abc123",
        "remote_path": "/Users/micllo/Documents/tools/apache-tomcat-8.0.21",
        "deploy_status": False,
        "deploy_time": "----",
        "deploy_log": "----",
        "deploy_result": "----",
        "apiTest_status": True,
        "apiTest_hostTag": "deploy_docker",
        "sonar_status": False,
        "sonar_key": "deploy",
        "sonar_name": "deploy",
        "sonar_version": "1.0",
        "sonar_sources": "src",
        "sonar_java_binaries": "target/classes",
        "jacoco_status": True,
        "jacoco_path": "/Users/micllo/Documents/works/jacoco",
        "progress": 0
    }
    module_info_list.append(proDemo1_deploy_uat_9)

    mycoll.insert_many(module_info_list)
    print(" 录 入 成 功 ！")


if __name__ == "__main__":
    pro_demo_1_uat()

    # http://127.0.0.1:4567/deploy/DeployApi/jacoco_test_01