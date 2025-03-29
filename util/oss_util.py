import os
import hashlib
import logging

logger = logging.getLogger(__name__)

class OSSUtil:
    """简化版 OSS 工具，不依赖特定的存储服务"""
    
    def __init__(self):
        # 可以在这里初始化云存储配置
        pass
    
    def get_default_file_key(self, url):
        """根据 URL 生成唯一的文件键名"""
        return hashlib.md5(url.encode()).hexdigest() + ".png"
    
    def upload_file_to_r2(self, file_path, image_key):
        """模拟上传文件到存储服务，返回占位 URL"""
        logger.info(f"模拟上传文件: {file_path} -> {image_key}")
        # 返回一个通用的图标 URL
        return f"https://www.google.com/s2/favicons?domain={file_path.replace('./','').replace('_favicon.ico','')}"
    
    def generate_thumbnail_image(self, url, image_key):
        """生成缩略图，返回与原图相同的 URL"""
        return self.upload_file_to_r2("", image_key)
