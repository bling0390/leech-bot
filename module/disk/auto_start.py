"""
磁盘监控自动启动模块
负责在Bot启动时根据配置自动启动磁盘监控服务
"""

import asyncio
from loguru import logger
from config.config import DISK_MONITOR_AUTO_START, DISK_ALERT_ENABLED
from module.disk.services.disk_monitor import DiskMonitorService
from module.i18n import get_i18n_manager


# 全局监控服务实例
global_monitor_service = None


async def start_disk_monitor_if_enabled():
    """如果启用则启动磁盘监控服务"""
    global global_monitor_service
    
    i18n = get_i18n_manager()
    
    if not DISK_MONITOR_AUTO_START:
        disabled_msg = i18n.translate('disk.monitor.auto_start_disabled')
        logger.info(disabled_msg)
        return
        
    if not DISK_ALERT_ENABLED:
        alert_disabled_msg = i18n.translate('disk.monitor.alert_disabled')
        logger.info(alert_disabled_msg)
        return
        
    try:
        # 创建监控服务实例
        global_monitor_service = DiskMonitorService()
        
        # 在后台启动监控
        asyncio.create_task(global_monitor_service.start_monitoring())
        
        success_msg = i18n.translate('disk.monitor.auto_start_success')
        logger.success(
            f"{success_msg} "
            f"(阈值: {global_monitor_service.threshold_gb}GB, "
            f"间隔: {global_monitor_service.check_interval}秒)"
        )
        
    except Exception as e:
        error_msg = i18n.translate('disk.monitor.auto_start_failed', error=str(e))
        logger.error(error_msg)


def stop_global_monitor_service():
    """停止全局监控服务"""
    global global_monitor_service
    
    if global_monitor_service and global_monitor_service.running:
        global_monitor_service.stop_monitoring()
        logger.info("全局磁盘监控服务已停止")
        
    # 清空全局服务实例
    global_monitor_service = None
        
        
def get_global_monitor_service():
    """获取全局监控服务实例"""
    return global_monitor_service


def is_monitor_service_running():
    """检查监控服务是否正在运行"""
    global global_monitor_service
    return global_monitor_service and global_monitor_service.running