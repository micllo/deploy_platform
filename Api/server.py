# -*- coding: utf-8 -*-
# import sys
# sys.path.append("./")
from Api.api_services.api_interface import *


@flask_app.route("/")
def server_index():
    server_info = "deploy_platform：V1.0.00R20210602"
    return server_info


if __name__ == '__main__':
    flask_app.run(host="0.0.0.0", port=3311, debug=False)

