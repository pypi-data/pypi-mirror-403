from typing import List

from bs4 import BeautifulSoup
from ..eagle import EagleApi


class EagleFolder(EagleApi):
    '''Eagle - 文件夹'''

    def __init__(self, host,token):
        super().__init__(host,token)

    def create_folder(self, folder_name: str, parent_id: str = None):
        '''创建文件夹'''
        data = {"folderName": folder_name,}
        params = {
            "token": self.token
        }
        if parent_id:
            data["parent"] = parent_id
        url = f"{self.host}/api/folder/create"
        resp = self.ask.post(url=url, json=data,params=params).json()
        self.verify_response("创建文件夹", resp)
        return resp['data']

    def query_folder_list(self):
        '''获取当前库的文件夹列表'''
        url = f"{self.host}/api/folder/list"
        params = {
            "token": self.token
        }
        resp = self.ask.get(url=url,params=params).json()
        self.verify_response("获取文件夹列表", resp)
        return resp['data']
