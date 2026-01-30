import time
from typing import List

from bs4 import BeautifulSoup
from ..eagle import EagleApi


class EagleFile(EagleApi):
    '''Eagle - 文件'''

    def __init__(self, host):
        super().__init__(host)

    def query_folder_files(self, folder_ids: List[str]):
        '''获取文件夹中的所有文件'''
        url = f"{self.host}/api/item/list"
        params = {
            "folders": ",".join(folder_ids)
        }
        resp = self.ask.get(url=url, params=params).json()
        self.verify_response("获取文件夹中的所有文件", resp)
        return resp['data']

    def get_file_info(self, file_id: str):
        '''获取指定文件的信息'''
        url = f"{self.host}/api/item/info"
        params = {"id": file_id}
        resp = self.ask.get(url=url, params=params).json()
        self.verify_response("获取指定文件的信息", resp)
        return resp['data']

    def add_from_paths(self, file_items: list, folder_id: str):
        '''
        将多个本地文件添加到 Eagle App
        :param file_items: [
                {
                    "path": "C://Users/User/Downloads/test.jpg",
                    "name": "アルトリア･キャスター",
                    "website": "https://www.pixiv.net/artworks/83585181",
                    "tags": ["FGO", "アルトリア・キャスター"],
                    "annotation": "久坂んむり"
                },
                {
                    "path": "C://Users/User/Downloads/test2.jpg",
                    "name": "アルトリア･キャスター",
                    "website": "https://www.pixiv.net/artworks/83585181",
                    "tags": ["FGO", "アルトリア・キャスター"],
                    "annotation": "久坂んむり"
                }
            ]
        :param folder_id:
        :return:
        '''
        data = {
            "items": file_items,
            "folderId": folder_id
        }
        url = f"{self.host}/api/item/addFromPaths"
        resp = self.ask.post(url=url, json=data).json()
        self.verify_response("将多个本地文件添加到 Eagle App", resp)
        return resp['status']
