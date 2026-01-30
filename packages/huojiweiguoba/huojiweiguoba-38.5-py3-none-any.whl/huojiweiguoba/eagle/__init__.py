import base64
import time
from pathlib import Path
from typing import Literal

from ..apis import Api

HEADERS = {}


class EagleApi(Api):
    plat_name = "Eagle"

    def __init__(self, host):
        self.host: str = host
        super().__init__()

    def verify_response(self, title: str, response: dict, type: Literal["status", "status_chinese"] = "status"):
        '''验证响应'''
        if type == "status":
            assert response[
                       'status'] == "success", f"{self.plat_name}【{title}】错误信息：{response['message'] if 'message' in response else response}"
        elif type == "status_chinese":
            assert response['status'] == "成功", f"{self.plat_name}【{title}】错误信息：{response['message'] if 'message' in response else response}"
        else:
            raise ValueError(f"verify_response type {type} not implemented")

    def application_info(self):
        '''获取APP信息'''
        url = f"{self.host}/api/application/info"
        resp = self.ask.get(url=url).json()
        self.verify_response("获取APP信息", resp)
        return resp['data']




