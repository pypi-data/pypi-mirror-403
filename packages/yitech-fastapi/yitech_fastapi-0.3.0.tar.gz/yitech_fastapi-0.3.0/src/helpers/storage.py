from typing import BinaryIO, Optional, Any


class YiBaseStorage:
    """文件存储服务基类"""
    
    async def upload_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream",
        path: str = "",
    ) -> str:
        """
        上传文件
        
        Args:
            file_obj: 文件对象
            filename: 文件名
            content_type: 文件内容类型
            path: 文件存储路径
        
        Returns:
            str: 文件访问URL
        """
        raise NotImplementedError
    
    async def download_file(self, file_url: str) -> BinaryIO:
        """
        下载文件
        
        Args:
            file_url: 文件访问URL
        
        Returns:
            BinaryIO: 文件对象
        """
        raise NotImplementedError
    
    async def delete_file(self, file_url: str) -> bool:
        """
        删除文件
        
        Args:
            file_url: 文件访问URL
        
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        raise NotImplementedError
    
    async def get_file_info(self, file_url: str) -> Optional[dict]:
        """
        获取文件信息
        
        Args:
            file_url: 文件访问URL
        
        Returns:
            Optional[dict]: 文件信息字典，包含文件名、大小、内容类型等
        """
        raise NotImplementedError


class YiLocalStorage(YiBaseStorage):
    """本地文件存储服务，用于开发环境"""
    
    def __init__(self, base_path: str = "./uploads"):
        """
        初始化本地文件存储服务
        
        Args:
            base_path: 本地存储基础路径
        """
        self.base_path = base_path
        import os
        os.makedirs(base_path, exist_ok=True)
    
    async def upload_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream",
        path: str = "",
    ) -> str:
        """上传文件到本地"""
        import os
        import uuid
        
        # 生成唯一文件名，避免冲突
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # 创建完整的文件路径
        full_path = os.path.join(self.base_path, path)
        os.makedirs(full_path, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(full_path, unique_filename)
        with open(file_path, "wb") as f:
            f.write(file_obj.read())
        
        # 返回文件URL（本地开发环境使用相对路径）
        return f"/uploads/{path}/{unique_filename}"
    
    async def download_file(self, file_url: str) -> BinaryIO:
        """从本地下载文件"""
        import os
        
        # 从URL中提取文件路径
        file_path = file_url.replace("/uploads/", "")
        full_path = os.path.join(self.base_path, file_path)
        
        # 打开文件
        return open(full_path, "rb")
    
    async def delete_file(self, file_url: str) -> bool:
        """从本地删除文件"""
        import os
        
        try:
            # 从URL中提取文件路径
            file_path = file_url.replace("/uploads/", "")
            full_path = os.path.join(self.base_path, file_path)
            
            # 删除文件
            os.remove(full_path)
            return True
        except Exception:
            return False
    
    async def get_file_info(self, file_url: str) -> Optional[dict]:
        """获取本地文件信息"""
        import os
        
        try:
            # 从URL中提取文件路径
            file_path = file_url.replace("/uploads/", "")
            full_path = os.path.join(self.base_path, file_path)
            
            # 获取文件信息
            stat = os.stat(full_path)
            return {
                "filename": os.path.basename(full_path),
                "size": stat.st_size,
                "modified_at": stat.st_mtime,
                "content_type": "application/octet-stream",  # 本地存储无法直接获取content_type
            }
        except Exception:
            return None


class YiS3Storage(YiBaseStorage):
    """AWS S3存储服务实现"""
    
    def __init__(self, bucket_name: str, region: str, aws_access_key: str, aws_secret_key: str):
        """
        初始化S3存储服务
        
        Args:
            bucket_name: S3存储桶名称
            region: AWS区域
            aws_access_key: AWS访问密钥
            aws_secret_key: AWS秘密密钥
        """
        self.bucket_name = bucket_name
        self.region = region
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        # 这里可以初始化S3客户端
    
    async def upload_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream",
        path: str = "",
    ) -> str:
        """上传文件到S3"""
        # TODO: 实现S3文件上传逻辑
        file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{path}/{filename}"
        print(f"[S3] 上传文件到: {file_url}")
        return file_url
    
    async def download_file(self, file_url: str) -> BinaryIO:
        """从S3下载文件"""
        # TODO: 实现S3文件下载逻辑
        print(f"[S3] 下载文件: {file_url}")
        # 返回一个模拟的文件对象
        import io
        return io.BytesIO("模拟文件内容".encode('utf-8'))
    
    async def delete_file(self, file_url: str) -> bool:
        """从S3删除文件"""
        # TODO: 实现S3文件删除逻辑
        print(f"[S3] 删除文件: {file_url}")
        return True
    
    async def get_file_info(self, file_url: str) -> Optional[dict]:
        """获取S3文件信息"""
        # TODO: 实现S3文件信息获取逻辑
        print(f"[S3] 获取文件信息: {file_url}")
        return {
            "filename": "example.txt",
            "size": 1024,
            "modified_at": 1609459200,
            "content_type": "text/plain",
        }


# 存储服务工厂函数
def yi_create_storage(storage_type: str = "local", **kwargs: Any) -> YiBaseStorage:
    """
    创建存储服务实例
    
    Args:
        storage_type: 存储服务类型，可选值：local, s3
        **kwargs: 存储服务的配置参数
    
    Returns:
        YiBaseStorage: 存储服务实例
    """
    if storage_type == "local":
        return YiLocalStorage(**kwargs)
    elif storage_type == "s3":
        return YiS3Storage(**kwargs)
    else:
        raise ValueError(f"不支持的存储服务类型: {storage_type}")


# 默认存储服务实例
yi_storage = yi_create_storage()
