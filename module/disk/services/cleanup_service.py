import os
import shutil
import asyncio
from typing import Dict, List
from pathlib import Path
from loguru import logger
from datetime import datetime, timedelta
from config.config import BOT_DOWNLOAD_LOCATION


class CleanupService:
    """磁盘清理服务"""
    
    def __init__(self, config: Dict = None):
        """初始化清理服务
        
        Args:
            config: 配置字典
        """
        if config:
            self.download_location = config.get('BOT_DOWNLOAD_LOCATION', BOT_DOWNLOAD_LOCATION)
        else:
            self.download_location = BOT_DOWNLOAD_LOCATION
            
    def calculate_directory_size(self, path: str) -> int:
        """计算目录大小
        
        Args:
            path: 目录路径
            
        Returns:
            目录大小（字节）
        """
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception as e:
            logger.error(f"计算目录大小失败: {e}")
            
        return total_size
        
    async def clean_download_directory(self) -> Dict:
        """清空下载目录
        
        Returns:
            清理结果
        """
        try:
            if not os.path.exists(self.download_location):
                return {
                    'success': False,
                    'message': f'下载目录不存在: {self.download_location}'
                }
                
            # 计算清理前的大小
            size_before = self.calculate_directory_size(self.download_location)
            size_before_gb = size_before / (1024**3)
            
            # 清空目录
            logger.info(f"开始清理下载目录: {self.download_location}")
            
            # 删除目录内容但保留目录本身
            for filename in os.listdir(self.download_location):
                file_path = os.path.join(self.download_location, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    logger.error(f"删除 {file_path} 失败: {e}")
                    
            # 或者完全删除并重建目录
            # shutil.rmtree(self.download_location)
            # os.makedirs(self.download_location, exist_ok=True)
            
            logger.success(f"下载目录清理完成，释放空间: {size_before_gb:.2f}GB")
            
            return {
                'success': True,
                'message': '下载目录已清空',
                'freed_space_gb': round(size_before_gb, 2),
                'location': self.download_location
            }
            
        except Exception as e:
            logger.error(f"清理下载目录失败: {e}")
            return {
                'success': False,
                'message': f'清理失败: {str(e)}'
            }
            
    async def clean_old_files(self, days: int = 7) -> Dict:
        """清理超过指定天数的旧文件
        
        Args:
            days: 文件保留天数
            
        Returns:
            清理结果
        """
        try:
            if not os.path.exists(self.download_location):
                return {
                    'success': False,
                    'message': f'下载目录不存在: {self.download_location}'
                }
                
            cutoff_time = datetime.now() - timedelta(days=days)
            removed_files = []
            total_freed = 0
            
            for root, dirs, files in os.walk(self.download_location):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    try:
                        # 获取文件修改时间
                        file_stat = os.stat(file_path)
                        file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
                        
                        if file_mtime < cutoff_time:
                            file_size = file_stat.st_size
                            os.unlink(file_path)
                            removed_files.append(filename)
                            total_freed += file_size
                            logger.debug(f"删除旧文件: {filename}")
                            
                    except Exception as e:
                        logger.error(f"处理文件 {file_path} 失败: {e}")
                        
            total_freed_gb = total_freed / (1024**3)
            
            logger.info(f"清理完成，删除 {len(removed_files)} 个文件，释放 {total_freed_gb:.2f}GB")
            
            return {
                'success': True,
                'message': f'已删除 {len(removed_files)} 个超过 {days} 天的文件',
                'freed_space_gb': round(total_freed_gb, 2),
                'removed_count': len(removed_files)
            }
            
        except Exception as e:
            logger.error(f"清理旧文件失败: {e}")
            return {
                'success': False,
                'message': f'清理失败: {str(e)}'
            }
            
    async def get_directory_info(self) -> Dict:
        """获取下载目录信息
        
        Returns:
            目录信息
        """
        try:
            if not os.path.exists(self.download_location):
                return {
                    'exists': False,
                    'location': self.download_location
                }
                
            total_size = self.calculate_directory_size(self.download_location)
            
            # 统计文件数量和类型
            file_count = 0
            dir_count = 0
            file_types = {}
            
            for root, dirs, files in os.walk(self.download_location):
                dir_count += len(dirs)
                file_count += len(files)
                
                for filename in files:
                    ext = Path(filename).suffix.lower()
                    if ext:
                        file_types[ext] = file_types.get(ext, 0) + 1
                        
            return {
                'exists': True,
                'location': self.download_location,
                'total_size_gb': round(total_size / (1024**3), 2),
                'file_count': file_count,
                'dir_count': dir_count,
                'file_types': file_types
            }
            
        except Exception as e:
            logger.error(f"获取目录信息失败: {e}")
            return {
                'error': str(e)
            }