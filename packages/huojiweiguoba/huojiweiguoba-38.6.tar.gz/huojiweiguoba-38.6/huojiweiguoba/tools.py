import configparser
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Union

def find_images_in_folder(folder_path: str) -> List[str]:
    """
    查找指定文件夹中的所有图片文件（仅第一级，不递归）

    Args:
        folder_path: 文件夹路径

    Returns:
        图片文件绝对路径列表
    """
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"文件夹不存在: {folder_path}")

    if not os.path.isdir(folder_path):
        raise NotADirectoryError(f"路径不是文件夹: {folder_path}")

    # 常见图片格式（可根据需要扩展）
    image_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
        '.webp', '.svg', '.ico', '.jfif', '.pjpeg', '.pjp',
        '.heic', '.heif', '.raw', '.cr2', '.nef', '.arw'
    }

    image_files = []

    # 获取文件夹下的所有文件和子文件夹名
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)

        # 只处理文件，跳过子文件夹
        if os.path.isfile(item_path):
            # 获取文件扩展名并转为小写
            file_ext = os.path.splitext(item)[1].lower()

            # 检查是否是图片文件
            if file_ext in image_extensions:
                image_files.append(item_path)

    return image_files


def rename_file(
        file_path: Union[str, Path],
        new_name: str,
        keep_extension: bool = True,
        overwrite: bool = False
) -> bool:
    """
    重命名单个文件

    Args:
        file_path: 文件路径
        new_name: 新的文件名（可包含扩展名）
        keep_extension: 是否保留原扩展名
        overwrite: 是否覆盖已存在的文件

    Returns:
        bool: 是否重命名成功
    """
    try:
        file_path = Path(file_path)

        # 检查文件是否存在
        if not file_path.exists():
            print(f"错误: 文件不存在 - {file_path}")
            return False

        if not file_path.is_file():
            print(f"错误: 不是文件 - {file_path}")
            return False

        # 获取原文件的目录和扩展名
        parent_dir = file_path.parent
        original_ext = file_path.suffix

        # 处理新文件名
        new_name_path = Path(new_name)

        if keep_extension and not new_name_path.suffix:
            # 新名称没有扩展名，添加原扩展名
            if not new_name.endswith(original_ext):
                new_name = f"{new_name}{original_ext}"

        # 构建新路径
        new_path = parent_dir / new_name

        # 检查目标文件是否已存在
        if new_path.exists() and not overwrite:
            print(f"错误: 目标文件已存在 - {new_path}")
            return False

        # 执行重命名
        file_path.rename(new_path)
        print(f"成功重命名: {file_path.name} -> {new_path.name}")
        return True

    except Exception as e:
        print(f"重命名文件时出错: {e}")
        return False