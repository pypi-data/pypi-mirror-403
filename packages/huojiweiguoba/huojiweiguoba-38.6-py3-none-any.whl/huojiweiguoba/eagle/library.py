from typing import List

from bs4 import BeautifulSoup
from ..eagle import EagleApi

class EagleLibrary(EagleApi):
    '''Eagle - 库'''

    def __init__(self, host):
        super().__init__(host)

    def get_library_info(self):
        '''获取库信息'''
        url = f"{self.host}/api/library/info"
        resp = self.ask.get(url=url).json()
        self.verify_response("获取库信息", resp)
        return resp['data']

    def get_library_history(self):
        '''获取应用程序最近打开的库列表。'''
        url = f"{self.host}/api/library/history"
        resp = self.ask.get(url=url).json()
        self.verify_response("获取应用程序最近打开的库列表", resp)
        return resp['data']

    def switch_library(self,libraryPath:str):
        '''切换 Eagle 当前打开的库'''
        data = {"libraryPath": libraryPath}
        url = f"{self.host}/api/library/switch"
        resp = self.ask.post(url=url, json=data).json()
        print(f"切换Eagl库至 「{libraryPath}」：{resp}")
        self.verify_response("切换库", resp)
        return resp