import os
import oss2
from datetime import datetime
import uuid

def generate_unique_filename(original_filename):
    """生成唯一文件名"""
    name, ext = os.path.splitext(original_filename)
    unique_id = str(uuid.uuid4())[:8]  # 取UUID前8位
    return f"{name}_{unique_id}{ext}"


class OSSUploader:
    """
    阿里云 OSS 文件上传器（带更多功能）
    """

    def __init__(self, access_key_id, access_key_secret, bucket_name, endpoint=None):
        """
        初始化 OSS 客户端

        参数:
            access_key_id: 阿里云 AccessKey ID
            access_key_secret: 阿里云 AccessKey Secret
            bucket_name: OSS 存储桶名称
            endpoint: OSS 访问域名（如：https://oss-cn-hangzhou.aliyuncs.com）
        """
        # 验证必要参数
        if not all([access_key_id, access_key_secret, bucket_name]):
            raise ValueError("access_key_id, access_key_secret 和 bucket_name 是必填参数")

        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.bucket_name = bucket_name

        # 如果未提供 endpoint，使用默认格式
        if endpoint is None:
            # 从 bucket_name 提取 region（假设 bucket_name 格式为 bucket-region）
            if '-' in bucket_name:
                region = bucket_name.split('-')[-1]
                self.endpoint = f'https://oss-{region}.aliyuncs.com'
            else:
                # 默认使用杭州区域
                self.endpoint = 'https://oss-cn-hangzhou.aliyuncs.com'
        else:
            self.endpoint = endpoint

        # 初始化 OSS 客户端
        self.auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket = oss2.Bucket(self.auth, self.endpoint, bucket_name)

        # 测试连接
        self._test_connection()

    def _test_connection(self):
        """测试 OSS 连接是否正常"""
        try:
            # 尝试获取 Bucket 信息
            self.bucket.get_bucket_info()
            print(f"OSS 连接成功 | Bucket: {self.bucket_name} | Endpoint: {self.endpoint}")
            return True
        except Exception as e:
            print(f"OSS 连接失败: {str(e)}")
            raise

    def upload_file_enhanced(self, local_file_path, oss_object_key=None, use_date_folder=True,
                             filename_strategy='uuid', custom_prefix=''):
        """
        上传文件到 OSS（增强版）

        参数:
            local_file_path: 本地文件路径
            oss_object_key: OSS 对象键（路径），如果为 None 则自动生成
            use_date_folder: 是否使用日期文件夹
            filename_strategy: 文件名生成策略
                - 'uuid': 使用UUID（默认）
                - 'timestamp': 使用时间戳
                - 'original': 使用原始文件名
                - 'mixed': UUID + 原始文件名前缀
            custom_prefix: 自定义文件名前缀

        返回:
            成功返回 OSS 对象的 URL，失败返回 None
        """
        # 1. 检查本地文件
        if not os.path.isfile(local_file_path):
            print(f"错误：'{local_file_path}' 不是一个有效的文件")
            return None

        # 2. 生成 OSS 对象键
        if oss_object_key is None:
            original_filename = os.path.basename(local_file_path)

            # 提取文件名和扩展名
            name, ext = os.path.splitext(original_filename)

            # 根据策略生成新文件名
            if filename_strategy == 'uuid':
                new_name = uuid.uuid4().hex
            elif filename_strategy == 'timestamp':
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                new_name = f"{timestamp}"
            elif filename_strategy == 'original':
                new_name = original_filename.replace(ext, '')  # 去掉扩展名
            elif filename_strategy == 'mixed':
                # 组合原始文件名和UUID（取前8位）
                short_uuid = uuid.uuid4().hex[:8]
                new_name = f"{name}_{short_uuid}"
            else:
                new_name = uuid.uuid4().hex  # 默认使用UUID

            # 添加自定义前缀
            if custom_prefix:
                new_name = f"{custom_prefix}_{new_name}"

            # 重新组合文件名和扩展名
            new_filename = f"{new_name}{ext}"

            # 构建完整路径
            if use_date_folder:
                date_str = datetime.now().strftime('%Y/%m/%d')
                oss_object_key = f"{date_str}/{new_filename}"
            else:
                oss_object_key = new_filename

        # 3. 获取文件信息
        file_size = os.path.getsize(local_file_path)
        print(f"开始上传: {local_file_path}")
        print(f"文件大小: {self._format_size(file_size)}")
        print(f"目标路径: {oss_object_key}")
        print(f"生成策略: {filename_strategy}")

        try:
            # 4. 执行上传
            result = self.bucket.put_object_from_file(oss_object_key, local_file_path)

            # 5. 检查上传结果
            if result.status == 200:
                # 构建访问 URL
                url = f"{self.endpoint.replace('https://', 'https://' + self.bucket_name + '.')}/{oss_object_key}"
                print(f"上传成功 | ETag: {result.etag}")
                print(f"访问链接: {url}")
                return url
            else:
                print(f"上传失败，HTTP状态码: {result.status}")
                return None

        except oss2.exceptions.OssError as e:
            print(f"OSS 服务错误: {e}")
            return None
        except Exception as e:
            print(f"上传过程中发生未知错误: {str(e)}")
            return None

    def upload_multiple_files(self, file_paths, base_folder="uploads"):
        """
        批量上传多个文件

        参数:
            file_paths: 本地文件路径列表
            base_folder: OSS 中的基础文件夹

        返回:
            成功上传的文件信息列表
        """
        results = []

        for i, file_path in enumerate(file_paths):
            print(f"\n上传文件 {i + 1}/{len(file_paths)}: {os.path.basename(file_path)}")

            # 为每个文件生成唯一的对象键
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime('%H%M%S')
            unique_name = f"{filename.rsplit('.', 1)[0]}_{timestamp}.{filename.rsplit('.', 1)[1] if '.' in filename else ''}"
            oss_object_key = f"{base_folder}/{unique_name}"

            # 上传文件
            url = self.upload_file(file_path, oss_object_key, use_date_folder=False)

            if url:
                results.append({
                    'local_path': file_path,
                    'oss_path': oss_object_key,
                    'url': url
                })

        print(f"\n批量上传完成: {len(results)}/{len(file_paths)} 个文件成功")
        return results

    def _format_size(self, size_bytes):
        """格式化文件大小显示"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"



# 使用示例
# if __name__ == "__main__":
#     Aliyun_access_key = ""
#     Aliyun_access_secret = ""
#     Aliyun_oss_bucket_name = ""
#     Aliyun_oss_endpoint = ""
#     oss_aliyun = OSSUploader(
#         access_key_id=Aliyun_access_key,  # 替换为你的 AccessKey ID
#         access_key_secret=Aliyun_access_secret,  # 替换为你的 AccessKey Secret
#         bucket_name=Aliyun_oss_bucket_name,  # 替换为你的 Bucket 名称
#         endpoint=Aliyun_oss_endpoint  # 可选，如果不提供会自动生成
#     )
#
#     # 示例 1: 基本使用
#     print("=== 示例 1: 基本使用 ===")
#
#     # 直接传入你的阿里云 OSS 凭证
#
#     # 上传单个文件
#     result = oss_aliyun.upload_file_enhanced(r"/Volumes/图片库-汽配/Eagle/AutoParts.library/images/MKC7I5LCOO8YG.info/主图_10.jpg")
#     print(result)
#
#     # # 示例 2: 指定 OSS 路径
#     # print("\n=== 示例 2: 指定 OSS 路径 ===")
#     # result = uploader.upload_file(
#     #     local_file_path="example.txt",
#     #     oss_object_key="documents/important/example.txt"
#     # )
#     #
#     # # 示例 3: 批量上传
#     # print("\n=== 示例 3: 批量上传 ===")
#     # files_to_upload = ["file1.txt", "file2.jpg", "file3.pdf"]
#     #
#     # # 在实际使用前，先检查文件是否存在
#     # existing_files = [f for f in files_to_upload if os.path.exists(f)]
#     #
#     # if existing_files:
#     #     results = uploader.upload_multiple_files(existing_files, "batch_uploads")
#     #     for r in results:
#     #         print(f"已上传: {r['local_path']} -> {r['oss_path']}")
#     # else:
#     #     print("测试文件不存在，跳过批量上传示例")