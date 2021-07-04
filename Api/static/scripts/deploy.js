/**
 * 修改部署状态（单个）
 */
function update_deploy_status(pro_name, nginx_api_proxy, deploy_name, _id) {
    // 调用ajax请求(同步)
    var request_url = "/" + nginx_api_proxy + "/DEPLOY/set_deploy_status/" + pro_name + "/" + deploy_name + "/" + _id
    var response_info = request_interface_url_v2(url=request_url, method="GET", async=false);
    if(response_info != "请求失败"){
        if(response_info.msg.search("运行中") != -1 ){
             setTimeout(function(){location.reload();}, 500);
        }else{
            if(response_info.data.new_deploy_status == true){
                $("#deploy_status_" + _id).html("上 线");
                $("#deploy_status_" + _id).attr('style', "width:50px;color:#00A600;display:table-cell;vertical-align:middle;");
            }else{
                $("#deploy_status_" + _id).html("下 线");
                $("#deploy_status_" + _id).attr('style', "width:50px;color:#DC143C;display:table-cell;vertical-align:middle;");
            }
        }
    }
}



/**
 *  填充编辑弹框（ 编辑之前 ）
 */
function fill_edit_frame(pro_name, nginx_api_proxy, _id, sonar_url, jacoco_report_url, apiTest_report_url) {

    // 将按钮禁灰不可点击
    $("#edit_btn").attr('disabled', true);

    // 调用ajax请求(同步)
    var request_url = "/" + nginx_api_proxy + "/DEPLOY/get_module_info/" + pro_name + "?_id=" + _id
    var response_info = request_interface_url_v2(url=request_url, method="GET", async=false);
    if(response_info != "请求失败"){
        var deploy_module_dict = response_info.deploy_module_dict
        console.log("module_name  -> " + deploy_module_dict.module_name)

        // 填充内容
        $("#deploy_id_edit").text(_id);
        $("#deploy_name_edit").text(deploy_module_dict.deploy_name);

        $("#build_env_edit").val(deploy_module_dict.build_env);
        $("#serial_num_edit").val(deploy_module_dict.serial_num);
        $("#branch_edit").val(deploy_module_dict.branch);

        if(deploy_module_dict.run_status == "True"){
            $("#run_status_edit").text("正在运行");
        }else{
            $("#run_status_edit").text("未运行");
        }
        $("#deploy_type_edit").text(deploy_module_dict.deploy_type);
        $("#deploy_file_edit").text(deploy_module_dict.deploy_file);
        $("#remote_path_edit").text(deploy_module_dict.remote_path);

        $("#apiTest_status_edit").val(deploy_module_dict.apiTest_status);
        $("#apiTest_hostTag_edit").val(deploy_module_dict.apiTest_hostTag);
        $("#apiTest_report_edit").text(apiTest_report_url + deploy_module_dict.module_name)
        $("#apiTest_report_edit").attr("href", apiTest_report_url + deploy_module_dict.module_name);

        $("#sonar_status_edit").val(deploy_module_dict.sonar_status);
        $("#sonar_key_edit").text(deploy_module_dict.sonar_key);
        $("#sonar_name_edit").text(deploy_module_dict.sonar_name);
        $("#sonar_version_edit").text(deploy_module_dict.sonar_version);
        $("#sonar_sources_edit").text(deploy_module_dict.sonar_sources);
        $("#sonar_java_binaries_edit").text(deploy_module_dict.sonar_java_binaries);
        $("#sonar_url_edit").text(sonar_url + deploy_module_dict.sonar_key);
        $("#sonar_url_edit").attr("href", sonar_url + deploy_module_dict.sonar_key);

        if(deploy_module_dict.jacoco_status == "True"){
            $("#jacoco_status_edit").text("开启");
            $("#jacoco_path_edit").text(deploy_module_dict.jacoco_path);
            $("#jacoco_url_edit").text(jacoco_report_url + deploy_module_dict.module_name + "/report/index.html");
            $("#jacoco_url_edit").attr("href", jacoco_report_url + deploy_module_dict.module_name + "/report/index.html");
        }else{
            $("#jacoco_status_edit").text("关闭");
            $("#jacoco_path_edit").text("");
            $("#jacoco_url_edit").text("");
        }
    }

    // 将按钮还原可点击
    $("#edit_btn").attr('disabled', false);
}


/**
 *  编辑部署信息
 */
function edit_deploy_info(pro_name, nginx_api_proxy) {

    // 获取相应的添加内容
    var _id = $("#deploy_id_edit").html().trim();
    var build_env = $("#build_env_edit").val().trim();
    var serial_num = $("#serial_num_edit").val().trim();
    var branch = $("#branch_edit").val().trim();
    var sonar_status = $("#sonar_status_edit").val().trim();
    var apiTest_status = $("#apiTest_status_edit").val().trim();
    var apiTest_hostTag = $("#apiTest_hostTag_edit").val().trim();

    var edit_dict = {"_id": _id, "build_env": build_env, "serial_num": serial_num, "branch": branch,
                     "sonar_status":sonar_status, "apiTest_status":apiTest_status, "apiTest_hostTag":apiTest_hostTag}

    // 调用ajax请求(同步)
    var request_url = "/" + nginx_api_proxy + "/DEPLOY/edit_deploy_info/" + pro_name
    var response_info = request_interface_url_v2(url=request_url, method="POST", data=edit_dict, async=false);
    if(response_info == "请求失败") {
        swal({text: response_info, type: "error", confirmButtonText: "知道了"});
    }else{
        var msg = response_info.msg;
        if (msg.search("成功") != -1){
            swal({text: response_info.msg, type: "success", confirmButtonText: "知道了"});
            setTimeout(function(){location.reload();}, 1000);
        }else {
            swal({text: response_info.msg, type: "error", confirmButtonText: "知道了"});
            if (msg.search("运行中") != -1){
                setTimeout(function(){location.reload();}, 2000);
            }
        }
    }
}


/**
 *  单个部署
 */
function single_deploy(pro_name, nginx_api_proxy, deploy_name, exec_type) {
    // 将按钮禁灰不可点击
    $("#deploy_btn").attr('disabled', true);

    swal({
        title: deploy_name + "\n确定要部署吗?",
        text: "",
        type: "warning",
        showCancelButton: true,
        confirmButtonText: "确定",
        cancelButtonText: "取消"
    }).then(function(isConfirm){
        if (isConfirm) {
            var request_url = "/" + nginx_api_proxy + "/DEPLOY/single_deploy/" + exec_type + "/" + pro_name + "/" + deploy_name
            var response_info = request_interface_url_v2(url=request_url, method="POST", async=false);
            if(response_info == "请求失败") {
                swal({text: response_info, type: "error", confirmButtonText: "知道了"});
            }else{
                var msg = response_info.msg;
                if (msg.search("部署进行中") != -1){
                    swal({text: response_info.msg, type: "success", confirmButtonText: "知道了"});
                    setTimeout(function(){location.reload();}, 3000);
                }else {
                    swal({text: response_info.msg, type: "error", confirmButtonText: "知道了"});
                    if (msg.search("上次部署还在进行中") != -1){
                        setTimeout(function(){location.reload();}, 3000);
                    }
                }
            }
        }
    }).catch((e) => {
        console.log(e)
        console.log("cancel");
    });

    // 将按钮还原可点击
    $("#deploy_btn").attr('disabled', false);
}


/**
 *  统计测试覆盖率
 */
function jacoco_exec(pro_name, nginx_api_proxy, deploy_name) {
    // 将按钮禁灰不可点击
    $("#jacoco_btn").attr('disabled', true);

    swal({
        title: deploy_name + "\n模块统计覆盖率?",
        text: "",
        type: "warning",
        showCancelButton: true,
        confirmButtonText: "确定",
        cancelButtonText: "取消"
    }).then(function(isConfirm){
        if (isConfirm) {
            var request_url = "/" + nginx_api_proxy + "/DEPLOY/get_jacoco_report/" + pro_name + "/" + deploy_name
            var response_info = request_interface_url_v2(url=request_url, method="GET", async=false);
            if(response_info == "请求失败") {
                swal({text: response_info, type: "error", confirmButtonText: "知道了"});
            }else{
                var msg = response_info.msg;
                if (msg.search("测试覆盖率报告更新中") != -1){
                    swal({text: response_info.msg, type: "success", confirmButtonText: "知道了"});
                    setTimeout(function(){location.reload();}, 5000);
                }else {
                    swal({text: response_info.msg, type: "error", confirmButtonText: "知道了"});
                }
            }
        }
    }).catch((e) => {
        console.log(e)
        console.log("cancel");
    });

    // 将按钮还原可点击
    $("#jacoco_btn").attr('disabled', false);
}


/**
 *  更新 模块 进度信息
 *
 *  1.判断是否存在运行中的模块
 *    2.遍历模块名称列表，找到运行中的模块
 *      3.轮询获取该模块的进度信息，并修改该模块页面显示进度
 *      4.当进度完成后，刷新页面
 */
function update_module_progress(pro_name, nginx_api_proxy, module_is_run, deploy_name_list_str) {
    if(module_is_run == "True"){
        // 将模块名称列表字符串 转换成 列表
        var deploy_name_list = deploy_name_list_str.split(",");
        $.each(deploy_name_list, function(n, deploy_name) {
            var request_url = "/" + nginx_api_proxy + "/DEPLOY/get_moudule_progress/" + pro_name + "/" + deploy_name;
            var response1 = request_interface_url_v2(url=request_url, method="GET", async=false);
            var run_status = response1.run_status;
            // 若该模块正在运行中，则轮询修改进度信息
            if(run_status == true){
                // 轮询修改进度信息
                var interval = setInterval(function () {  // 间隔指定的毫秒数 不停地执行指定的代码，定时器
                    // 更新 用例'运行状态、开始时间、运行时间'
                    var response2 = request_interface_url_v2(url=request_url, method="GET", async=false);
                    var id = response2._id
                    var progress = response2.progress
                    var run_status = response2.run_status;

                    // ------ 修改 部署结果 ------
                    $('#deploy_result_' + id).empty();  // 清空<td id='deploy_result_{id}'>元素内容
                    $('#exec_result_' + id).remove();   // 删除<span id='exec_result_{id}'>元素
                    // 在<td id='deploy_result_{id}'>元素下添加<span id='exec_result_{id}'>子元素
                    var span = document.createElement('span');
                    span.setAttribute('id', 'exec_result_' + id);
                    document.getElementById('deploy_result_' + id).appendChild(span);
                    // 重新赋值
                    $("#exec_result_" + id).html("部 署 中 ...");
                    $("#exec_result_" + id).attr('style', "font-size:14px");
                    $("#exec_result_" + id).removeClass().addClass("label label-warning");

                    // ------ 清空 部署时间 ------
                    $('#deploy_time_' + id).empty();

                    // ------ 修改 操作（更新进度条） ------
                    if(run_status == true){
                        if(progress < 100){
                            // 更新进度条记录
                            $("#progress_bar_" + id).css({"width": progress + "%"}); // 方式一：修改css样式（修改的是'style'属性中的内容）
                            // $("#progress_bar_" + id).attr("style", "width:" + progress + "%");  // 方式二：修改属性
                            // 更新进度条样式
                            $("#progress_bar_" + id).attr("class", "progress progress-striped active");
                            if(progress > 0 && progress <= 25 ){
                                $("#progress_bar_" + id).attr("class", "progress-bar progress-bar-danger");
                            }else if(progress > 25 && progress <= 50 ){
                                $("#progress_bar_" + id).attr("class", "progress-bar progress-bar-warning");
                            }else{
                                $("#progress_bar_" + id).attr("class", "progress-bar progress-bar-success");
                            }
                        }else{
                            clearInterval(interval); // 用于停止 setInterval() 方法执行的函数代码
                            location.reload();
                        }
                    }else{
                        clearInterval(interval); // 用于停止 setInterval() 方法执行的函数代码
                        location.reload();
                    }
                }, 1000);
            }
        });
    }


}
