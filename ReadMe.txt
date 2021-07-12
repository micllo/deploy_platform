
【 注 意 事 项 】

1.新增项目时
（1）需要在'Config > pro_config.py'文件中 配置 项目名称列表（ 目的：关联项目模板 ）
（2）需要给不同项目添加'批量部署状态'配置
     执行 docker_pro_config.py 中的脚本

2.新增部署模块时
（1）需要在'Mongo_exec'的对应环境中添加部署模块信息入数据库
（2）部署流程中各模块的不同配置，需要修改'Common > deploy_flow.py'文件中'区分项目'的地方
（3）若新模块是java项目，则需要进行Jacoco代码测试覆盖率的JVM配置
    1）War包：配置在tomcat中
    2）Jar包：通过命令配置



########################################################################################################################


【 本 地 配 置 项 目 开 发 环 境 】

1.配置本地 venv 虚拟环境
（1）修改：requirements_init.txt
（2）删除：原有 venv 目录
（3）执行：sh -x venv_install.sh

2.配置 gulpfile 依赖
（1）修改：gulpfile_install.sh
（2）删除：原有的 package.json 文件
（3）执行：sh -x gulpfile_install.sh

3.配置 Nginx -> deploy_platform.conf

upstream api_server_deploy{
  server 127.0.0.1:3301 weight=1 max_fails=2 fail_timeout=30s;
  ip_hash;
}

server {
  listen 3310;
  server_name localhost;

  location /deploy_report_local/ {
        sendfile off;
        expires off;
        gzip on;
        gzip_min_length 1000;
        gzip_buffers 4 8k;
        gzip_types application/json application/javascript application/x-javascript text/css application/xml;
        add_header Cache-Control no-cache;
        add_header Cache-Control 'no-store';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header REMOTE-HOST $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
        alias /Users/micllo/Documents/works/GitHub/deploy_platform/Reports/;
       }

   location /jacoco_report_local/ {
        sendfile off;
        expires off;
        gzip on;
        gzip_min_length 1000;
        gzip_buffers 4 8k;
        gzip_types application/json application/javascript application/x-javascript text/css application/xml;
        add_header Cache-Control no-cache;
        add_header Cache-Control 'no-store';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header REMOTE-HOST $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
        alias /Users/micllo/Documents/works/GitHub/deploy_platform/Jacoco_Report/;
       }

  location /api_local/ {
         proxy_set_header Host $host;
         proxy_set_header X-Real-IP $remote_addr;
         proxy_set_header REMOTE-HOST $remote_addr;
         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
         proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504 http_404;
         proxy_pass http://api_server_deploy/;
         #proxy_pass http://127.0.0.1:3301/;
         proxy_redirect default;
  }
}


【 备 注 】
MAC本地安装的 nginx 相关路径
默认安装路径：/usr/local/Cellar/nginx/1.15.5/
默认配置文件路径：/usr/local/etc/nginx/
日志：/Users/micllo/nginx_logs/access.log
     /Users/micllo/nginx_logs/error.log;
sudo nginx
sudo nginx -t
sudo nginx -s reload

########################################################################################################################


【 本地 Mac 相关 】

1.uWSGI配置文件：./vassals/mac_app_uwsgi.ini
（1）启动 uWSGI 命令 在 ./start_uwsgi_local.sh 脚本
（2）停止 uWSGI 命令 在 ./stop_uwsgi.sh 脚本

2.上传 GitHub 需要被忽略的文件
（1）Logs、workspace、Jacoco_Report -> 临时生成的 日志、部署根路径、代码覆盖率报告目录
（2）vassals_local、venv -> 本地的 uWSGI配置、python3虚拟环境
（3）node_modules、gulpfile.js、package.json、package-lock.json -> 供本地启动使用的gulp工具

3.访问地址（ server.py 启动 ）：
（1）接口地址 -> http://127.0.0.1:3311/
               http://127.0.0.1:3311/API/index
               http://127.0.0.1:3311/API/DEPLOY/show_deploy_log/<pro_name>

4.访问地址（ uwsgi 启动 ）：
（1）页面首页 -> http://localhost:3310/api_local/DEPLOY/index
（2）部署日志 -> http://localhost:3310/api_local/DEPLOY/show_deploy_log/<pro_name>
（3）接口地址 -> http://localhost:3310/api_local/DEPLOY/xxxxxxx
   （ 备注：uwgsi 启动 3301 端口、nginx 配置 3310 反向代理 3301 ）

5.本地相关服务的启动操作（ gulpfile.js 文件 ）
（1）启动服务并调试页面：gulp "html debug"
（2）停止服务命令：gulp "stop env"
（3）部署docker服务：gulp "deploy docker"


【 虚拟环境添加依赖 】
1.创建虚拟环境：virtualenv -p /usr/local/bin/python3 venv （-p：指明python3所在目录）
2.切换到虚拟环境：source venv/bin/activate
3.退出虚拟环境：deactivate
4.添加依赖：
pip3 install -v flask==0.12 -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com


########################################################################################################################


【 Docker Centos7 相关 】

1.uWSGI配置文件：vassals_docker/app_uwsgi.ini
（1）启动 uWSGI 命令 在 ./start_uwsgi.sh 脚本
（2）停止 uWSGI 命令 在 ./stop_uwsgi.sh 脚本

2.服务器目录结构
  /var/log/uwsgi/ 		       -> pid_uwsgi.pid、app_uwsgi.log、emperor.log
  /var/log/nginx/ 		       -> error.log、access.log
  /etc/uwsgi/vassals/	       -> app_uwsgi.ini
  /opt/project/logs/ 	       -> 项目日志
  /opt/project/${pro_name}     -> 项目
  /opt/project/workspace/      -> 部署项目根路径
  /opt/project/Jacoco_Report/  -> 代码覆盖率报告目录
  /opt/project/tmp             -> 临时目录(部署时使用)

3.服务器部署命令：
（1）从GitGub上拉取代码至临时目录
（2）关闭nginx、mongo、uwsgi服务
（3）替换项目、uwsgi.ini配置文件
（4）替换env_config配置文件
（5）启动nginx、mongo、uwsgi服务
（6）清空临时文件

4.部署时的存放位置：
（1）./deploy_platform -> /opt/project/deploy_platform
（2）./deploy_platform/vassals/app_uwsgi.ini -> /etc/uwsgi/vassals/app_uwsgi.ini

5.部署时相关配置文件的替换操作：
（1）将./Env/目录下的 env_config.py 删除
（2）将./Env/目录下的 env_config_docker.py 重命名为 env_config.py

6.访问地址（ Docker 内部 ）：
（1）页面首页 -> http://127.0.0.1:80/api/DEPLOY/index
（2）部署日志 -> http://127.0.0.1:80/api/DEPLOY/show_deploy_log/<pro_name>
（3）接口地址 -> http://127.0.0.1:80/api/DEPLOY/xxxxxxx
    ( 备注：uwgsi 启动 8081 端口、nginx 配置 80 反向代理 8081 )

7.访问地址（ 外部访问 ）：
（1）页面首页 -> http://192.168.31.9:1680/api/DEPLOY/index
（2）测试报告 -> http://192.168.31.9:1680/api/DEPLOY/show_deploy_log/<pro_name>
（3）接口地址 -> http://192.168.31.9:1680/api/DEPLOY/xxxxxxx
    ( 备注：docker 配置 1680 映射 80 )

8.关于部署
  通过'fabric'工具进行部署 -> deploy.py
    （1）将本地代码拷贝入临时文件夹，并删除不需要的文件目录
    （2）将临时文件夹中的该项目压缩打包，上传至服务器的临时文件夹中
    （3）在服务器中进行部署操作：停止nginx、mongo、uwsgi服务 -> 替换项目、uwsgi.ini配置文件 -> 替换config配置文件 -> 启动nginx、mongo、uwsgi服务
    （4）删除本地的临时文件夹
  'gulp'命令 执行 deploy.py 文件 进行部署


########################################################################################################################


【 框 架 结 构 】（ 提高代码的：可读性、重用性、易扩展性 ）
 1.Api层：       对外接口、原静态文件
 2.Build层：     编译后的静态文件
 3.Common层：    通用方法、部署流程类
 4.Config层：    错误码映射、定时任务、项目配置
 5.Env层：       环境配置
 6.Mongo_exec层：部署模块的配置信息（保存入数据库）
 7.Tools层：     工具函数
 8.其他：
 （1）tmp/ -> 临时存放上传的用例Excel文件
 （2）api_case_tmpl.xlsx  -> 供页面下载的测试用例模板文件
 （3）vassals/ -> 服务器的'uWSGI配置'
 （4）vassals_local/、venv/ -> 本地的'uWSGI配置、python3虚拟环境'
 （5）Logs/、workspace/、Jacoco_Report/ -> 临时生产的 日志、部署根路径、代码覆盖率报告目录
 （6）node_modules/、gulpfile.js、package.json、package-lock.json -> 供本地启动使用的gulp工具
 （7）deploy.py、start_uwsgi_local.sh、stop_uwsgi_local.sh、tmp_uwsgi_pid.txt -> 本地部署文件及相关命令和临时文件


【 功 能 点 】

1.项目用途
（1）部署生产环境：通过批量部署功能，一键部署上线的项目模块
（2）部署测试环境：每个项目模块可以单独部署，并提供部署接口配置GitLab的Webhooks实现自动部署

2.页面功能
（1）相关配置：
      上下线状态、部署序号、部署分支、是否需要API自动化测试、是否需要Sonar扫描、是否需要Jacoco检测测试覆盖率
（2）相关功能：
      单独部署、批量部署、查看部署日志、实时显示部署进度、部署完成发送钉钉通知

3.部署流程
（1）本地拉取代码  （必须）
（2）本地构建     （必须）
（3）上传服务器    （必须）
（4）服务器端操作  （必须）
（5）Sonar静态代码扫描  （可选）
（6）API接口自动化测试   （可选）
（7）Jacoco测试覆盖率报告（可选，仅限java项目）

4.定时任务
（1）删除过期(一周前)的文件：日志



【 框 架 工 具 】
 Python3 + Flask + uWSGI + Nginx + Bootstrap + MongoDB + Docker + Fabric + Gulp + Sonar + Jacoco

1.使用 Flask ：
（1）提供 相关测试接口、页面接口

2.使用 Nginx ：
（1）提供 用例模板、最新报告 的下载地址
（2）反向代理 相关接口

3.使用 uWSGI :
（1）用作 web 服务器
（2）使用'emperor'命令进行管理：监视和批量启停 vassals 目录下 uwsgi 相关的 .ini 文件

4.使用 Docker：
（1）使用Dockerfile构建centos7镜像：提供项目所需的相关配置环境
（2）使用'docker-compose' 一键管理多个容器

5.使用 MongoDB ：
（1）保存测试用例

6.使用 Fabric ：
（1）配置相关脚本，实现一键部署

7.使用 NodeJS 的 Gulp 命令 ：
（1）配置本地启动的相关服务，实现一键启动或停止
（2）编译静态文件，防止浏览器缓存js问题
（3）实时监听本地调试页面功能

8.使用 Sonar ：
（1）对代码进行静态扫描

9.使用 Jacoco ：
（1）针对Java代码执行代码测试覆盖率统计
