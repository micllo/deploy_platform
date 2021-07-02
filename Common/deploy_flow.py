# -*- coding:utf-8 -*-
from Env import env_config as cfg
import os, time
from Common.com_func import is_null, log, deploy_monitor_send_DD, mkdir

from fabric.api import *
from fabric.api import env
from io import StringIO
from Tools.date_helper import get_current_timestamp
import traceback

"""
     【 部 署 流 程 】
        1.本地操作（通过SSH方式，为了捕获异常信息）
        （1）创建本地workspace目录
        （2）删除原有项目（ 文件夹、tar包 ）
        （3）拉取代码 
        （4）构建（ mave|npm|压缩 ）
        （5）检查：
              拉取代码是否成功（ gitlab库连接超时、部署分支不存在 ）
              构建是否成功
              部署文件是否存在
        2.上传部署文件
        3.服务器端操作（解压、配置、重启服务）
        （1）解压
        （2）配置
        （3）重启服务
        （4）检查：
              服务器中最新的部署文件时间戳应该要大于部署前创建的时间戳
              重启服务前后的进程ID是否完全不一样
        4.Sonar扫描 <可选项>（本地操作）
        5.启动Jacoco服务（仅针对Java项目） <可选项>
        6.接口自动化测试 <可选项>
        7.生成Jacoco代码覆盖率报告（仅针对Java项目）<可选项>
        8.部署结果 发送钉钉
        
        《 备 注 》
        本地拉取代码的操作 仍然使用SSH登录服务器的方式（登录本地服务器），是为了将操作步骤显示在部署日志中
        若不采用该方式，则无法将操作步骤记录在部署日志中


       < 进 度 条 步 骤 >
         1.本地拉取代码（必须）
         2.本地构建   （必须）
         3.上传服务器  （必须）
         4.服务器端操作（必须）
         5.sonar扫描    （可选）
         6.接口自动化测试 （可选）
         7.生成jacoco报告（可选）


"""


class FabricException(Exception):
    """ 自定义捕获 Fabric 异常方法 """
    pass


env.abort_exception = FabricException
env.warn_only = False        # 显示错误，终止执行
env.abort_on_prompts = True  # Fabric 将以非交互模式运行（解决：密码错误进行交互的问题）


class deployPro(object):

    def __init__(self, pro_name, module_name, deploy_name, branch, build_env, deploy_type, deploy_file,
                 ssh_user, ssh_passwd, ssh_host, ssh_port, remote_path, exec_type, deploy_time, apiTest_status,
                 apiTest_hostTag, sonar_status, sonar_key, sonar_name, sonar_version, sonar_sources,
                 sonar_java_binaries, jacoco_status, jacoco_path):
        self.pro_name = pro_name        # 项目名称
        self.module_name = module_name  # 模块名称（前端模块，后端模块）
        self.deploy_name = deploy_name  # 部署名称（项目名称-模块名称-构建环境-服务器后3位）eg：MagicWallet-srvTimer-wuxiA-160
        self.branch = branch            # 部署分支
        self.build_env = build_env      # 构建环境
        self.deploy_type = deploy_type  # 部署类型（ Nginx |  War |  Jar | Python ）
        self.deploy_file = deploy_file  # 部署文件（ .zip  | .war | .jar | .tar.gz ）
        self.deploy_time = deploy_time  # 部署时间
        self.ssh_user = ssh_user      # 服务器 用户名
        self.ssh_passwd = ssh_passwd  # 服务器 密码
        self.ssh_host = ssh_host      # 服务器 地址
        self.ssh_port = ssh_port      # 服务器 端口
        self.remote_path = remote_path  # 服务器 远程路径
        self.exec_type = exec_type      # 执行方式（ manual | gitlab ）
        self.current_time = 0    # 部署前 当前的时间戳
        self.file_time = 0       # 部署后 部署文件的创建时间戳
        self.current_pid = None  # 部署前 PID（ 可能有多个，比如Python的uwsgi ）
        self.deploy_pid = None   # 部署后 PID
        self.output = StringIO()    # 输出信息
        self.exception_info = None  # 获取异常信息
        self.deploy_result = None   # 部署结果
        self.sonar_log = None       # sonar日志
        self.deploy_log = ""        # 部署日志

        # API 测试
        self.apiTest_status = apiTest_status        # API测试状态（是否启用）
        self.apiTest_hostTag = apiTest_hostTag      # API测试 host标记（ 与测试平台保持一致 ）

        # Sonar 静态代码扫描
        self.sonar_status = sonar_status                # Sonar 状态（是否启用）
        self.sonar_key = sonar_key                      # 检测项目的唯一标识
        self.sonar_name = sonar_name                    # 被检测项目的名称
        self.sonar_version = sonar_version              # 被检测项目的版本
        self.sonar_sources = sonar_sources              # 被检测项目的源代码目录
        self.sonar_java_binaries = sonar_java_binaries  # 被检测项目的二进制文件

        # Jacoco 测试覆盖率统计（ 仅针对Java项目 ）
        self.jacoco_status = jacoco_status              # Jacoco 状态（是否启用）
        self.jacoco_path = jacoco_path                  # Jacoco 路径

        # 进度相关
        self.progress = 0   # 当前进度（初始化）
        self.increment = 0  # 进度增量（初始化）
        self.get_progress_config()

    def __del__(self):
        """ 销毁实例对象 """
        self.output.close()

    def get_progress_config(self):
        """
            获取进度配置
            1.计算 步骤总数
            2.计算 进度增量
        """
        setp_num = 4  # 初始化必要步骤
        if self.sonar_status:
            setp_num += 1
        if self.apiTest_status:
            setp_num += 1
        if self.jacoco_status:
            setp_num += 1
        self.increment = int(100/setp_num)

    def calculate_progress(self):
        """ 计算当前进度 """
        self.progress += self.increment
        self.deploy_log += "\n当前进度：" + str(self.progress) + " %\n"

    def complete_deploy_log(self):
        """ 完善 部署日志 """
        self.deploy_log += "\n\n################# 部 署 信 息 #################\n"
        self.deploy_log += "\n部署前 当前的时间戳    -> " + str(self.current_time) + "\n"
        self.deploy_log += "\n部署后 部署文件的时间戳 -> " + str(self.file_time) + "\n"
        self.deploy_log += "\n部署前 进程PID -> " + str(self.current_pid) + "\n"
        self.deploy_log += "\n部署后 进程PID -> " + str(self.deploy_pid) + "\n"
        self.deploy_log += "\n部 署 时 间 -> " + self.deploy_time + "\n"
        self.deploy_log += "\n部 署 结 果 -> " + self.deploy_result + "\n"
        self.deploy_log += "\n\n########################### 显 示 异 常 信 息 ###########################\n"
        self.deploy_log += "\n" + str(self.exception_info) + "\n"
        self.deploy_log += "\n\n########################### 显 示 输 出 信 息 ###########################\n"
        self.deploy_log += "\n" + self.output.getvalue() + "\n"
        self.deploy_log += "\n\n########################### 显 示 Sonar 信 息 ###########################\n"
        self.deploy_log += "\n" + str(self.sonar_log) + "\n"

    def clean_output(self):
        """ 清除 输出日志 """
        self.output.close()
        self.output = StringIO()

    def custom_run(self, cmd, warn_only=False, pty=True, stdout_flag=False, clean_output=False):
        """
        自定义 Fabric 中的 run() 方法
        :param cmd:           Linux 命令
        :param warn_only:     默认 显示错误信息，并终止后续执行
        :param pty:           默认 创建伪终端
        :param stdout_flag:   默认 不获取输出日志
        :param clean_output:  默认 不清除输出日志
        :return:
        """
        self.deploy_log += cmd + "\n"
        if stdout_flag:
            run_res = run(cmd, warn_only=warn_only, pty=pty, stdout=self.output)
        else:
            run_res = run(cmd, warn_only=warn_only, pty=pty)
        # 清除 输出日志
        if clean_output:
            self.clean_output()
        return run_res

    def local_opt_step_common(self):
        """ 本地操作步骤（共同）"""
        self.deploy_log += "\n本地操作：删除原有项目（ 文件夹、部署文件 ）\n"
        self.custom_run("rm -rf " + self.deploy_file)
        self.custom_run("rm -rf " + self.module_name)
        self.deploy_log += "\n本地操作：拉取代码\n"
        self.custom_run("git clone -b " + self.branch + " " + cfg.GITLAB_BASE_URL + self.module_name + ".git --depth 1",
                        stdout_flag=True)
        # 清除 输出日志
        self.clean_output()

    def check_pull_result(self):
        """
        检查：拉取代码是否成功（ gitlab库连接超时、部署分支不存在 ）
        :return:
        """
        if self.exception_info:
            if (self.output.getvalue().find("Failed to connect to") != -1 and
                self.output.getvalue().find("Operation timed out") != -1) or \
                    (self.output.getvalue().find("unable to access 'http") != -1 and
                     (self.output.getvalue().find("Couldn't connect to server") != -1 or
                      self.output.getvalue().find("Connection refused") != -1)):
                self.deploy_result = "拉取代码失败(gitlab库连接超时)"
            elif (self.output.getvalue().find("warning: Could not find remote branch " + self.branch + " to clone")) != -1:
                self.deploy_result = "拉取代码失败(部署分支不存在)"
            else:
                self.deploy_result = "本地操作(其他异常情况)"

    def check_deploy_file(self, deploy_file_path):
        """
        检查：部署文件是否存在
        :param deploy_file_path：部署文件全路径
        :return:
        """
        if is_null(self.deploy_result):
            if not os.path.exists(deploy_file_path):
                self.deploy_result = "部署文件不存在"

    def check_bulid_situation(self):
        """
        检查：构建是否成功
        :return: The requested profile "uat123" could not be activated because it does not exist
        """
        if is_null(self.deploy_result):
            if self.deploy_type in ["War", "Jar"]:
                if self.output.getvalue().find("BUILD SUCCESS") == -1 and \
                        self.output.getvalue().find("BUILD SUCCESSFUL") == -1 and \
                        self.output.getvalue().find("Build complete") == -1:
                    self.deploy_result = "构建失败"
                elif self.output.getvalue().find("The requested profile") != -1 and \
                        self.output.getvalue().find("could not be activated because it does not exist") != -1:
                    self.deploy_result = "构建失败(构建环境不存在)"

    def upload_deploy_file(self, deploy_file_path):
        """
        上传部署文件
        :param deploy_file_path：部署文件全路径
        :return:
        """
        if is_null(self.deploy_result):
            self.deploy_log += "\n上传文件(无输出信息)\n"
            try:
                with settings(host_string="%s@%s:%s" % (self.ssh_user, self.ssh_host, self.ssh_port),
                              password=self.ssh_passwd):
                    put(remote_path=self.remote_path + "/tmp/", local_path=deploy_file_path)
            except FabricException as e:
                self.exception_info = e
            if self.exception_info:
                if "Needed to prompt for a connection or sudo password" in str(self.exception_info):
                    self.deploy_result = "部署服务器用户名或密码错误"
                else:
                    self.deploy_result = "部署文件上传失败"

    def get_server_pid(self, cmd):
        """
        获取服务器PID
        （ 备注：可能有多个，比如Python的uwsgi ）
        """
        pid_attr = self.custom_run(cmd, warn_only=True)
        pid = self.deploy_type == "Python" and str(pid_attr).split("\r\n") or str(pid_attr)
        return pid

    def get_file_time(self):
        """
            获取部署文件创建时间戳
            Linux ： stat -c %Y
            Mac：ls -lU 当前时间
                 ls -lc 修改时间
        """
        if self.deploy_type == "War":  # 临时使用
            return int(self.custom_run("ls -lc " + self.remote_path + "/tmp/" + self.deploy_file + " | awk '{print $5}'",
                                       warn_only=True)) * 100
        else:
            return int(self.custom_run("stat -c %Y " + self.remote_path + "/tmp/" + self.deploy_file, warn_only=True))

    def check_deploy_info(self):
        """
           检查部署后的信息
            1.服务器中最新的部署文件时间戳应该要大于部署前创建的时间戳
            2.重启服务前后的进程ID是否完全不一样
        :return:
        """
        # 检查：部署文件时间戳
        self.deploy_result = self.file_time == 0 and "服务器的部署文件日期没有获取到" or \
                          (self.file_time < self.current_time and "服务器的部署文件日期不是最新的" or "")
        # 检查：进程PID
        if isinstance(self.deploy_pid, list):  # Python uwsgi 会启动多个pid
            if is_null(self.deploy_pid[0]):
                self.deploy_result = "服务器uWSGI进程ID没有获取到"
            else:
                if [pid for pid in self.deploy_pid if pid in self.current_pid]:
                    self.deploy_result = "服务器uWSGI进程ID没有改变"
        else:
            if is_null(self.deploy_pid):
                self.deploy_result = "服务器uWSGI进程ID没有获取到"
            else:
                if self.current_pid == self.deploy_pid:
                    self.deploy_result = "服务器uWSGI进程ID没有改变"

    def api_auto_test(self):
        """ API 接口自动化测试 """
        self.deploy_log += "\n-------- 执 行 API 接 口 测 试 --------\n"
        with settings(host_string="%s@%s:%s" % (cfg.LOCAL_USER, cfg.LOCAL_HOST, cfg.LOCAL_PORT),
                      password=cfg.LOCAL_PASSWD):
            self.custom_run("curl " + cfg.API_TEST_URL + "/" + self.apiTest_hostTag + "/" + self.module_name)

    def start_jacoco_server(self):
        """ 启动 Jacoco 监听服务 """
        self.deploy_log += "\n服务器端操作：启动 Jacoco 监听服务\n"
        try:
            with settings(host_string="%s@%s:%s" % (self.ssh_user, self.ssh_host, self.ssh_port),
                          password=self.ssh_passwd):
                with cd(self.jacoco_path):
                    self.custom_run("java -jar lib/jacococli.jar dump --address localhost --port 12345 "
                                    "--destfile report/jacoco.exec")
        except FabricException as e:
            self.exception_info = e

    def get_jacoco_report(self):
        """
        获取 测试覆盖率报告（仅针对Java项目）

        1.本地操作：准备 jacoco_report 下载目录 并清理原有内容
        2.服务端操作：生成覆盖率报告 并下载到本地
        （1）生成代码覆盖率的exec文件
        （2）根据exec文件生成测试覆盖率报告
        （3）将生成的报告下载到部署服务器
        3.本地操作：解压report目录

        :return:
        """
        try:
            time.sleep(5)  # API 自动化测试 是另起线程执行的

            self.deploy_log += "\n-------- 获取Jacoco测试覆盖率报告 --------\n"
            self.deploy_log += "本地操作目录 " + cfg.JACOCO_REPORT_DIR + self.module_name + "\n"
            self.deploy_log += "服务器端操作目录 " + self.jacoco_path + "\n"

            # 本地操作：准备 jacoco_report 下载目录 并清理原有内容
            mkdir(cfg.JACOCO_REPORT_DIR + self.module_name)  # 若目录不存在 则新增
            with settings(host_string="%s@%s:%s" % (cfg.LOCAL_USER, cfg.LOCAL_HOST, cfg.LOCAL_PORT),
                          password=cfg.LOCAL_PASSWD):
                with cd(cfg.JACOCO_REPORT_DIR + self.module_name):
                    self.deploy_log += "\n本地操作：清理原有内容 \n"
                    self.custom_run("rm -rf report")
                    self.custom_run("rm -rf report.tar.gz")

            # 服务端操作：生成覆盖率报告 并下载到本地
            with settings(host_string="%s@%s:%s" % (self.ssh_user, self.ssh_host, self.ssh_port),
                          password=self.ssh_passwd):
                with cd(self.jacoco_path):
                    self.deploy_log += "\n服务器端操作：清除原有内容、生成覆盖率报告、压缩、下载到本地\n"
                    self.custom_run("rm -rf report")
                    self.custom_run("rm -rf report.tar.gz")
                    self.custom_run("java -jar lib/jacococli.jar dump --address localhost --port 12345 "
                                    "--destfile report/jacoco.exec")
                    if self.deploy_type == "War":
                        self.custom_run("java -jar lib/jacococli.jar report report/jacoco.exec --classfiles " +
                                        self.remote_path + "/webapps/" + self.module_name + "/WEB-INF/classes" +
                                        " --html report")
                    time.sleep(2)
                    self.custom_run("tar -czvf report.tar.gz report", stdout_flag=True, clean_output=True)
                    get(remote_path="report.tar.gz", local_path=cfg.JACOCO_REPORT_DIR + self.module_name)

            # 本地操作：解压jacoco的report目录
            with settings(host_string="%s@%s:%s" % (cfg.LOCAL_USER, cfg.LOCAL_HOST, cfg.LOCAL_PORT),
                          password=cfg.LOCAL_PASSWD):
                with cd(cfg.JACOCO_REPORT_DIR + self.module_name):
                    self.deploy_log += "\n本地操作：解压报告\n"
                    self.custom_run("tar -xzvf report.tar.gz -C .", stdout_flag=True, clean_output=True)

        except FabricException as e:
            self.exception_info = e
            # log.info(traceback.print_exc())

    def run_deploy(self):
        self.deploy_log += "\n\n++++++++++++++++++++++++ " + self.deploy_name + " 部 署 开 始 ++++++++++++++++++++++++\n"
        # 1.本地操作（通过SSH方式，为了捕获异常信息）
        mkdir(cfg.WORKSPACE)  # 若目录不存在则创建
        try:
            with settings(host_string="%s@%s:%s" % (cfg.LOCAL_USER, cfg.LOCAL_HOST, cfg.LOCAL_PORT),
                          password=cfg.LOCAL_PASSWD):
                with cd(cfg.WORKSPACE):
                    self.local_opt_step_common()     # 本地操作步骤（共同）
                    self.calculate_progress()
                    self.local_opt_step_different()  # 本地操作步骤（区分项目）
                    self.calculate_progress()
        except FabricException as e:
            self.exception_info = e

        # 检查：拉取代码是否成功、构建是否成功、部署文件是否存在
        self.check_pull_result()
        self.check_bulid_situation()
        self.check_deploy_file(self.get_deploy_file_path())

        # 2.上传部署文件（获取当前时间戳）
        self.current_time = get_current_timestamp()
        self.upload_deploy_file(self.get_deploy_file_path())
        self.calculate_progress()

        # 3.服务器端操作（解压、配置、重启服务）
        if is_null(self.deploy_result):
            try:
                with settings(host_string="%s@%s:%s" % (self.ssh_user, self.ssh_host, self.ssh_port),
                              password=self.ssh_passwd):
                    self.deploy_log += "\n服务器端操作：获取部署前PID、部署文件创建时间戳\n"
                    self.current_pid = self.get_server_pid(self.get_server_pid_cmd())
                    self.file_time = self.get_file_time()
                    self.server_opt_step_different()  # 服务器操作步骤（区分项目）
                    time.sleep(5)
                    self.deploy_log += "\n服务器端操作：获取部署后PID\n"
                    self.deploy_pid = self.get_server_pid(self.get_server_pid_cmd())
            except FabricException as e:
                self.exception_info = e
            if self.exception_info:
                self.deploy_result = "服务器端操作有异常"
            else:
                self.check_deploy_info()  # 检查部署信息（ 部署文件时间戳、进程ID ）
            self.calculate_progress()

        if is_null(self.deploy_result):

            # 4.Sonar扫描（直接本地操作）<可选项>
            sonar_msg = ""
            if self.sonar_status:
                self.sonar_scan()  # Sonar 静态扫描（区分项目）
                if self.exception_info or self.sonar_log.find("Calculating CPD for 0 files") != -1:
                    sonar_msg = "(Sonar配置有误)"
                else:
                    if self.sonar_log.find("ANALYSIS SUCCESSFUL") == -1 or self.sonar_log.find("EXECUTION SUCCESS") == -1:
                        sonar_msg = "(Sonar扫描失败)"
                self.calculate_progress()

            # 5.启动Jacoco服务（仅针对Java项目） <可选项>
            if self.jacoco_status:
                self.start_jacoco_server()

            # 6.接口自动化测试 <可选项>
            if self.apiTest_status:
                self.api_auto_test()
                self.calculate_progress()

            # 7.生成Jacoco代码覆盖率报告（仅针对Java项目）<可选项>
            if self.jacoco_status:
                self.get_jacoco_report()
                self.calculate_progress()

            self.deploy_result = "部署成功" + sonar_msg
            self.deploy_log += "\n++++++++++++++++++++++++ " + self.deploy_name + \
                               " 部 署 成 功 ！！！ ++++++++++++++++++++++++\n"
        else:
            self.deploy_log += "\n++++++++++++++++++++++++ " + self.deploy_name + \
                               " 部 署 终 止 ？？？ ++++++++++++++++++++++++\n"
        # 完善部署日志
        self.complete_deploy_log()
        self.output.close()  # 释放StringIO缓冲区，执行此函数后，数据将被释放，也不可再进行操作
        self.progress = 100

        # 8.部署结果 发送钉钉
        deploy_monitor_send_DD(deploy_name=self.deploy_name, module_name=self.module_name, exec_type=self.exec_type,
                               deploy_host=self.ssh_host, branch=self.branch, build_env=self.build_env,
                               deploy_result=self.deploy_result, deploy_time=self.deploy_time,
                               sonar_status=self.sonar_status, sonar_key=self.sonar_key,
                               jacoco_status=self.jacoco_status, apiTest_status=self.apiTest_status)

    def local_opt_step_different(self):
        """ 本地操作步骤（区分项目） """
        if self.deploy_type == "Python":
            self.deploy_log += "\n本地操作：压缩部署文件 \n"
            self.custom_run("tar -czvf " + self.deploy_file + " " + self.module_name, stdout_flag=True, clean_output=True)
        if self.deploy_type == "War":
            self.deploy_log += "\n本地操作：构建war包 \n"
            with cd(cfg.WORKSPACE + self.module_name):
                self.custom_run("mvn clean package -P" + self.build_env, stdout_flag=True)

    def get_deploy_file_path(self):
        """ 获取部署文件路径（区分项目） """
        if self.deploy_type == "Python":
            return cfg.WORKSPACE + self.deploy_file
        if self.deploy_type == "War":
            return cfg.WORKSPACE + self.module_name + "/target/" + self.deploy_file

    def get_server_pid_cmd(self):
        """ 获取服务进程PID（区分项目） """
        if self.deploy_type == "Python":  # < PID 列表 >
            return "ps aux | grep uwsgi | grep -v 'grep' | awk '{print $2}'"
        if self.deploy_type == "War":
            return "ps aux | grep tomcat | grep -v 'grep' | grep -v 'sonar' | awk '{print $2}'"

    def sonar_scan(self):
        """
            Sonar 静态扫描（区分项目）
            1.在项目根目录下创建 sonar-project.properties 文件
            2.配置项目扫描内容
            3.执行扫描
        """
        try:
            with lcd(cfg.WORKSPACE + self.module_name):
                # 1.在项目根目录下创建 sonar-project.properties 文件
                local("rm -rf sonar-project.properties")
                local("touch sonar-project.properties")
                # 2.配置项目扫描内容
                local("echo 'sonar.projectKey=" + self.sonar_key + "' >> sonar-project.properties")
                local("echo 'sonar.projectName=" + self.sonar_name + "' >> sonar-project.properties")
                local("echo 'sonar.projectVersion=" + self.sonar_version + "' >> sonar-project.properties")
                local("echo 'sonar.sources=" + self.sonar_sources + "' >> sonar-project.properties")
                if self.deploy_type == "War":
                    local("echo 'sonar.java.binaries=" + self.sonar_java_binaries + "' >> sonar-project.properties")
                # 3.执行扫描
                self.sonar_log = local("sonar-scanner", capture=True)
        except FabricException as e:
            self.exception_info = e

    def server_opt_step_different(self):
        """ 服务器操作步骤（区分项目） """

        if self.deploy_type == "Python":

            self.deploy_log += "\n服务器端操作：停止'nginx、uwsgi'服务\n"
            self.custom_run("sh /home/centos/stop_nginx.sh", warn_only=True)
            self.custom_run("sh /home/centos/stop_uwsgi.sh", warn_only=True)
            # self.custom_run("pgrep mongod | sudo xargs kill -9", warn_only_flag=True)

            self.deploy_log += "\n服务器端操作：解压'部署文件'\n"
            self.custom_run("tar -xzvf " + self.remote_path + "/tmp/" + self.deploy_file + " -C " +
                            self.remote_path + "/tmp/", stdout_flag=True, clean_output=True)

            self.deploy_log += "\n服务器端操作：清除原有文件\n"
            self.custom_run("rm -rf " + self.remote_path + "/" + self.module_name)

            self.deploy_log += "\n服务器端操作：拷贝'项目'\n"
            self.custom_run("cp -r " + self.remote_path + "/tmp/" + self.module_name + " " + self.remote_path)

            self.deploy_log += "\n服务器端操作：替换'uwsgi.ini'配置文件\n"
            self.custom_run("rm -r /etc/uwsgi/vassals/*.ini")
            self.custom_run("cp -r " + self.remote_path + "/" + self.module_name + "/vassals/*.ini /etc/uwsgi/vassals/")

            self.deploy_log += "\n服务器端操作：替换Env环境配置文件\n"
            with cd(self.remote_path + "/" + self.module_name + "/Env"):
                self.custom_run("rm -r env_config.py && mv env_config_docker.py env_config.py")

            self.deploy_log += "\n服务器端操作：启动'nginx、uwsgi'服务\n"
            # self.custom_run("sudo mongod -f /tools/mongodb/bin/mongodb.conf", warn_only_flag=True)
            self.custom_run("sh /home/centos/start_nginx.sh", warn_only=True)
            self.custom_run("sh /home/centos/start_uwsgi.sh", warn_only=True, pty=False)
            # （ pty：解决'fabric'执行'nohub'的问题 ）

            self.deploy_log += "\n服务器端操作：清空临时文件夹\n"
            self.custom_run("rm -rf " + self.remote_path + "/tmp/" + self.module_name)
            self.custom_run("rm -rf " + self.remote_path + "/tmp/" + self.deploy_file)

        if self.deploy_type == "War":

            # 关闭tomcat前，需要先杀死 监听服务进程
            if self.jacoco_status:
                self.deploy_log += "\n服务器端操作：杀死'jacoco'监听服务进程\n"
                self.custom_run("lsof -i:12345 | awk '{print $2}' | sed -n '2p' | xargs kill -9")

            self.deploy_log += "\n服务器端操作：停止'tomcat'服务\n"
            self.custom_run("set -m;sh " + self.remote_path + "/bin/shutdown.sh")
            # fabric 启动 tomcat 命令前必须要加上 set -m;

            self.deploy_log += "\n服务器端操作：清除原有文件\n"
            self.custom_run("rm -rf " + self.remote_path + "/webapps/" + self.module_name)
            self.custom_run("rm -rf " + self.remote_path + "/webapps/" + self.deploy_file)

            self.deploy_log += "\n服务器端操作：移动部署文件到目标文件夹\n"
            self.custom_run("mv " + self.remote_path + "/tmp/" + self.deploy_file + " " + self.remote_path + "/webapps/")

            self.deploy_log += "\n服务器端操作：启动'tomcat'服务\n"
            self.custom_run("set -m;sh " + self.remote_path + "/bin/startup.sh")


if __name__ == "__main__":
    pass



