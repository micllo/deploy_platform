/**
 *   "查询部署日志"按钮
 *   (方法'serialize'获取的是form表单的input中的'name'和'value'对)
 */
function search(pro_name, nginx_api_proxy) {

    // 将按钮禁灰不可点击
    $("#search_btn").attr('disabled', true);

    // 获取相应的添加内容
    var deploy_name = $("#deploy_name").val().trim();
    console.log("deploy_name -> " + deploy_name)

    var request_url = "/" + nginx_api_proxy + "/DEPLOY/search_deploy_log?pro_name=" + pro_name + "&deploy_name=" + deploy_name
    var response_info = request_interface_url_v2(url=request_url, method="GET", async=false);
    if(response_info != "请求失败"){
        var msg = response_info.msg
        var deploy_log_list = response_info.deploy_log_list

        // ------ 清理 原有内容 ------
        // 删除<div id='show_deploy_info'>元素
        $('#show_deploy_info').remove();
        // 在<form id='show'>元素下添加<div id='show_deploy_info'>子元素
        var show_div = document.createElement('div');
        show_div.setAttribute('id', 'show_deploy_info');
        document.getElementById('show').appendChild(show_div);

        if (msg.search("成功") != -1){

            // 循环显示部署信息
            $.each(deploy_log_list, function (num, line) {
                var deployInfoHtml = "";
                deployInfoHtml += "<div class='row b g-info'><div class='col-sm-1'></div><div class='col-sm-10' align='left'><font size='3'>" + line + "</font></div></div>";
                $('#show_deploy_info').append(deployInfoHtml);
            })

            // 改变当前结果状态
            $("#search_result").html(msg);
            $("#search_result").removeClass().addClass("label label-success");
        }else{
            $("#search_result").html(msg);
            $("#search_result").removeClass().addClass("label label-danger");
        }

        // 将按钮还原可点击
        $("#search_btn").attr('disabled', false);
    }else{
        $("#search_result").html(response_info);
        $("#search_result").removeClass().addClass("label label-danger");
    }
}


// // 将按钮禁灰不可点击
// $("#stop_run_status").attr('disabled', true);
//
// // 改变当前结果状态
// $("#stop_run_status_result").html(" 处 理 中 。。。");
// $("#stop_run_status_result").removeClass().addClass("label label-info");
//
// $("#stop_run_status_result").html(response_info.msg);
// $("#stop_run_status_result").removeClass().addClass("label label-success");
// $("#stop_run_status_result").removeClass().addClass("label label-warning");
// $("#stop_run_status_result").removeClass().addClass("label label-danger");
//
// // 将按钮还原可点击
// $("#stop_run_status").removeattr('disabled');
// $("#stop_run_status").attr('disabled', false);

// readonly