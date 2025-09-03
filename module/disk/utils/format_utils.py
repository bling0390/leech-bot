"""
磁盘监控格式化工具
提供各种单位格式化功能
"""

from typing import Dict


def format_file_count(count: int) -> str:
    """格式化文件数量
    
    Args:
        count: 文件数量
        
    Returns:
        格式化的文件数量字符串
    """
    if count == 0:
        return "0个文件"
    elif count == 1:
        return "1个文件"
    else:
        # 添加千位分隔符
        return f"{count:,}个文件"


def format_directory_count(count: int) -> str:
    """格式化目录数量
    
    Args:
        count: 目录数量
        
    Returns:
        格式化的目录数量字符串
    """
    if count == 0:
        return "0个文件夹"
    elif count == 1:
        return "1个文件夹"
    else:
        return f"{count}个文件夹"


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        格式化的文件大小字符串
    """
    if size_bytes == 0:
        return "0B"
    elif size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024**2:
        return f"{size_bytes / 1024:.0f}KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes / 1024**2:.0f}MB"
    else:
        size_gb = size_bytes / 1024**3
        if size_gb == int(size_gb):
            return f"{int(size_gb)}GB"
        else:
            return f"{size_gb:.1f}GB"


def format_disk_info(disk_info: Dict) -> str:
    """格式化磁盘信息
    
    Args:
        disk_info: 磁盘信息字典
        
    Returns:
        格式化的磁盘信息字符串
    """
    free_space = disk_info.get('free_space_gb', 0)
    used_percent = disk_info.get('used_percent', 0)
    total_gb = disk_info.get('total_gb', 0)
    used_gb = disk_info.get('used_gb', 0)
    
    return (
        f"💾 剩余空间: {free_space}GB\n"
        f"📈 使用率: {used_percent}%\n"
        f"💿 总空间: {total_gb}GB\n"
        f"📂 已使用: {used_gb}GB"
    )


def format_directory_info(dir_info: Dict) -> str:
    """格式化目录信息
    
    Args:
        dir_info: 目录信息字典
        
    Returns:
        格式化的目录信息字符串
    """
    file_count = dir_info.get('file_count', 0)
    dir_count = dir_info.get('dir_count', 0)
    total_size_gb = dir_info.get('total_size_gb', 0)
    
    return (
        f"📁 {format_file_count(file_count)}\n"
        f"📂 {format_directory_count(dir_count)}\n"
        f"💾 占用空间: {total_size_gb}GB"
    )


def format_storage_size(size_gb: float, precision: int = 2) -> str:
    """格式化存储大小
    
    Args:
        size_gb: 大小（GB）
        precision: 小数位数
        
    Returns:
        格式化的存储大小
    """
    if size_gb < 0.01:
        # 转换为MB
        size_mb = size_gb * 1024
        if size_mb < 0.01:
            # 转换为KB
            size_kb = size_mb * 1024
            return f"{size_kb:.0f}KB"
        return f"{size_mb:.1f}MB"
    else:
        return f"{size_gb:.{precision}f}GB"


def format_percentage(value: float, precision: int = 1) -> str:
    """格式化百分比
    
    Args:
        value: 百分比值
        precision: 小数位数
        
    Returns:
        格式化的百分比字符串
    """
    return f"{value:.{precision}f}%"