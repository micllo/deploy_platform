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
function fill_edit_frame(pro_name, nginx_api_proxy, _id) {

    // 调用ajax请求(同步)
    var request_url = "/" + nginx_api_proxy + "/DEPLOY/get_module_info/" + pro_name + "?_id=" + _id
    var response_info = request_interface_url_v2(url=request_url, method="GET", async=false);
    if(response_info != "请求失败"){
        var deploy_module_dict = response_info.deploy_module_dict

        // 填充内容
        $("#deploy_id_edit").text(_id)
        $("#deploy_name_edit").text(deploy_module_dict.deploy_name);
        $("#build_env_edit").val(deploy_module_dict.build_env);
        $("#serial_num_edit").val(deploy_module_dict.serial_num);
        $("#branch_edit").val(deploy_module_dict.branch);

    }
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

    var edit_dict = {"_id": _id, "build_env": build_env, "serial_num": serial_num, "branch": branch}

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
    swal({
        title: "确定要部署 " + deploy_name + " 吗?",
        text: "",
        type: "warning",
        showCancelButton: true,
        confirmButtonText: "确定",
        cancelButtonText: "取消"
    }).then(function(isConfirm){
        if (isConfirm) {
            var data_dict = {"exec_type": exec_type, "pro_name": pro_name, "deploy_name": deploy_name}
            var request_url = "/" + nginx_api_proxy + "/DEPLOY/single_deploy"
            var response_info = request_interface_url_v2(url=request_url, method="POST", data=data_dict, async=false);
            if(response_info == "请求失败") {
                swal({text: response_info, type: "error", confirmButtonText: "知道了"});
            }else{
                var msg = response_info.msg;
                if (msg.search("部署进行中.....") != -1){
                    swal({text: response_info.msg, type: "success", confirmButtonText: "知道了"});
                    setTimeout(function(){location.reload();}, 1000);
                }else {
                    swal({text: response_info.msg, type: "error", confirmButtonText: "知道了"});
                    if (msg.search("上次部署还在进行中") != -1){
                        setTimeout(function(){location.reload();}, 5000);
                    }
                }
            }
        }
    }).catch((e) => {
        console.log(e)
        console.log("cancel");
    });
}


/**
 *  统计测试覆盖率
 */
function jacoco_exec(pro_name, nginx_api_proxy, deploy_name) {
    swal({
        title: "统计 " + deploy_name + " 模块覆盖率?",
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
}
