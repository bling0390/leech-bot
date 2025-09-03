"""
配置可用性检查模块

此模块提供各种服务和功能的可用性检查函数，
避免与其他模块产生循环导入问题。
"""

from config.config import ALIST_WEB, ALIST_TOKEN, ALIST_HOST


def is_alist_available() -> bool:
    """
    检查 AList 服务是否可用
    
    Returns:
        bool: 如果 AList 配置完整则返回 True，否则返回 False
    """
    return all([ALIST_WEB, ALIST_TOKEN]) or all([ALIST_HOST, ALIST_TOKEN])