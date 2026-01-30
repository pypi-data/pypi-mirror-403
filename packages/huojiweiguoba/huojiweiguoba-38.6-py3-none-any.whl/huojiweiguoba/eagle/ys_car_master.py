import os.path
from pathlib import Path

from ..apis.oss import OSSUploader
from ..eagle.library import EagleLibrary
from ..eagle.file import EagleFile
from ..eagle.folder import EagleFolder
from natsort import natsorted
from ..tools import find_images_in_folder


class Eagle(EagleFolder, EagleFile, EagleLibrary):

    def __init__(self,host:str, eagle_library_path: str):
        super().__init__(host)
        self.eagle_library_path = eagle_library_path
        # 获取当前library
        if self.get_library_info()['library']['path'] == self.eagle_library_path:
            print(f"[Eagle] 当前库正确,无须切换")
        else:
            switch_resp = self.switch_library(self.eagle_library_path)
            print(f"[Eagle] 库切换至 {self.eagle_library_path} ,Message:{switch_resp}")

    def create_local_image_path(self,image_id:str,image_name:str,image_ext:str):
        '''本地图片路径'''
        return os.path.join(self.eagle_library_path,"images",f"{image_id}.info",f"{image_name}.{image_ext}")


    def search_folder(self, shop_name: str, category: str, sku: str):
        '''搜索SPU文件夹'''
        # 获取店铺文件夹
        shop_folder_items = {_['name']: _ for _ in self.query_folder_list()}
        assert shop_name in shop_folder_items.keys(), f"[Eagle]: 店铺[{shop_name}]文件夹不存在"
        # 获取类目文件夹
        category_folder_items = {_['name']: _ for _ in shop_folder_items[shop_name]['children']}
        assert category in category_folder_items.keys(), f"[Eagle]: 店铺[{shop_name}] 类目[{category}]文件夹不存在"
        # 获取SKU文件夹
        sku_folder_items = {_['name']: _ for _ in category_folder_items[category]['children']}
        assert sku in sku_folder_items, f"[Eagle]: 店铺[{shop_name}] 类目[{category}] sku[{sku}]文件夹不存在"
        # 获取文件夹图片返回
        images_list = natsorted(self.query_folder_files([sku_folder_items[sku]['id']]), key=lambda x: x['name'])
        result = [{
            "name": _['name'],
            "local_path": f"{self.eagle_library_path}/images/{_['id']}.info/{_['name']}.{_['ext']}",
            "url": _['url']
        } for _ in images_list]
        return result

    def upload_white_background_image_folder(self, shop_name: str, category: str, oe_number: str, folder_path: str):
        # 获取店铺文件夹
        shop_folder_items = {_['name']: _ for _ in self.query_folder_list()}
        # 店铺文件夹不存在则创建
        if shop_name not in shop_folder_items.keys():
            create_shop_resp = self.create_folder(folder_name=shop_name)
            print(f"创建店铺文件夹:{create_shop_resp}")
        else:
            create_shop_resp = shop_folder_items[shop_name]

        # 获取类目文件夹
        category_folder_items = {_['name']: _ for _ in create_shop_resp['children']}
        if category not in category_folder_items.keys():
            create_category_resp = self.create_folder(folder_name=category, parent_id=create_shop_resp['id'])
            print(f"创建类目文件夹:{create_category_resp}")
        else:
            create_category_resp = category_folder_items[category]

        # 获取oe_number文件夹
        oe_number_folder_items = {_['name']: _ for _ in create_category_resp['children']}
        if oe_number not in oe_number_folder_items.keys():
            create_oe_number_resp = self.create_folder(folder_name=oe_number, parent_id=create_category_resp['id'])
            print(f"创建oe_number文件夹:{create_oe_number_resp}")
        else:
            create_oe_number_resp = oe_number_folder_items[oe_number]

        # 读取文件夹的所有图片上传至oe_number文件夹
        folder_images = find_images_in_folder(folder_path)
        folder_images = natsorted(folder_images,reverse=True)
        # 遍历上传
        file_items = []
        for _ in folder_images:
            file_items.append({
                "path": Path(_).__str__(),
                "name": Path(_).stem.__str__(),
            })
            print(f"{Path(_).stem.__str__()}上传成功")
        if len(file_items) > 0:
            self.add_from_paths(file_items=file_items, folder_id=create_oe_number_resp['id'])
            print(f"[{oe_number}]上传图片:{','.join([_['name'] for _ in file_items])}")

    def upload_sku_folder(self, shop_name: str, category: str, sku: str, folder_path: str,oss_aliyun:OSSUploader):
        # 获取店铺文件夹
        shop_folder_items = {_['name']: _ for _ in self.query_folder_list()}
        # 店铺文件夹不存在则创建
        if shop_name not in shop_folder_items.keys():
            create_shop_resp = self.create_folder(folder_name=shop_name)
            print(f"创建店铺文件夹:{create_shop_resp}")
        else:
            create_shop_resp = shop_folder_items[shop_name]

        # 获取类目文件夹
        category_folder_items = {_['name']: _ for _ in create_shop_resp['children']}
        if category not in category_folder_items.keys():
            create_category_resp = self.create_folder(folder_name=category, parent_id=create_shop_resp['id'])
            print(f"创建类目文件夹:{create_category_resp}")
        else:
            create_category_resp = category_folder_items[category]

        # 获取SKU文件夹
        sku_folder_items = {_['name']: _ for _ in create_category_resp['children']}
        if sku not in sku_folder_items.keys():
            create_sku_resp = self.create_folder(folder_name=sku, parent_id=create_category_resp['id'])
            print(f"创建SKU文件夹:{create_sku_resp}")
        else:
            create_sku_resp = sku_folder_items[sku]

        # 读取文件夹的所有图片上传至SKU文件夹
        folder_images = find_images_in_folder(folder_path)
        folder_images = [_ for _ in folder_images if f"{sku}_" in Path(_).stem.__str__()]
        # 遍历上传
        file_items = []
        for _ in folder_images:
            file_items.append({
                "path": Path(_).__str__(),
                "name": Path(_).stem.__str__(),
                "website": oss_aliyun.upload_file_enhanced(_)
            })
            print(f"{Path(_).stem.__str__()}上传成功")
        if len(file_items) > 0:
            self.add_from_paths(file_items=file_items, folder_id=create_sku_resp['id'])
            print(f"[{sku}]上传图片:{','.join([_['name'] for _ in file_items])}")


# eagle_api = Eagle(Eagle_Library)
#
# if __name__ == "__main__":
#     # AI作图脚本
#     ai_drawing_folder_path = r"/Volumes/影刀/car_axis_results"
#     for _ in os.listdir(ai_drawing_folder_path):
#         if not os.path.isdir(os.path.join(ai_drawing_folder_path,_)):continue
#         print(f"\n\n{_}")
#         imgs = find_images_in_folder(os.path.join(ai_drawing_folder_path,_))
#         for i in imgs:
#             if "_kit_part" in i.split('/')[-1]:
#                 rename_kit_part = rename_file(i,Path(i).name.__str__().replace("_kit_part","_2"),True,True)
#                 print(f"rename_kit_part",rename_kit_part)
#             if "_v3" in i.split('/')[-1]:
#                 rename_v3 = rename_file(i,Path(i).name.__str__().replace("_v3","_1"),True,True)
#                 print(f"rename_v3", rename_v3)
#         eagle_api.upload_sku_folder("Firstlink", "CV", _, os.path.join(ai_drawing_folder_path,_))
#     raise 1
#
#
#
#     # eagle_api = Eagle(Eagle_Library)
#     eagle_api.upload_sku_folder("Firstlink", "BC", "B2BC032", "/Users/hwj/Desktop/BC-images")
#     # print(eagle_api.search_folder(shop_name="Firstlink", category="BC", sku="BC10074"))
#     # print(eagle_api.search_folder(shop_name="Firstlink", category="BC", sku="通用图"))
#     pass
