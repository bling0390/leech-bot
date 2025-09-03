"""
网络相关的格式化工具函数
"""
from module.i18n.services.i18n_manager import I18nManager

# 初始化国际化管理器
i18n_manager = I18nManager()

def format_bandwidth(bytes_per_second: float) -> str:
    """格式化带宽显示
    
    Args:
        bytes_per_second: 每秒字节数
        
    Returns:
        格式化后的带宽字符串
    """
    if bytes_per_second < 1024:
        return f"{bytes_per_second:.1f} B/s"
    elif bytes_per_second < 1024 ** 2:
        return f"{bytes_per_second / 1024:.1f} KB/s"
    elif bytes_per_second < 1024 ** 3:
        return f"{bytes_per_second / (1024 ** 2):.1f} MB/s"
    else:
        return f"{bytes_per_second / (1024 ** 3):.1f} GB/s"


def format_data_size(bytes_count: int) -> str:
    """格式化数据大小显示
    
    Args:
        bytes_count: 字节数
        
    Returns:
        格式化后的大小字符串
    """
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 ** 2:
        return f"{bytes_count / 1024:.1f} KB"
    elif bytes_count < 1024 ** 3:
        return f"{bytes_count / (1024 ** 2):.1f} MB"
    else:
        return f"{bytes_count / (1024 ** 3):.1f} GB"


def format_packet_count(count: int) -> str:
    """格式化数据包数量显示
    
    Args:
        count: 数据包数量
        
    Returns:
        格式化后的数量字符串
    """
    if count < 1000:
        return f"{count}"
    elif count < 1000000:
        return f"{count / 1000:.1f}K"
    else:
        return f"{count / 1000000:.1f}M"


def format_uptime(seconds: float, language: str = 'zh_CN') -> str:
    """格式化运行时间
    
    Args:
        seconds: 秒数
        language: 语言代码
        
    Returns:
        格式化后的时间字符串
    """
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    
    days_text = i18n_manager.translate('network.format.days', language)
    hours_text = i18n_manager.translate('network.format.hours', language)
    minutes_text = i18n_manager.translate('network.format.minutes', language)
    
    if days > 0:
        return f"{days}{days_text}{hours}{hours_text}{minutes}{minutes_text}"
    elif hours > 0:
        return f"{hours}{hours_text}{minutes}{minutes_text}"
    else:
        return f"{minutes}{minutes_text}"