import os
import asyncio
import psutil
from datetime import datetime
from typing import Dict, Optional
from loguru import logger
from config.config import BOT_DOWNLOAD_LOCATION
from module.disk.utils.format_utils import format_storage_size
from module.i18n import get_i18n_manager


class DiskMonitorService:
    """磁盘空间监控服务"""
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化磁盘监控服务
        
        Args:
            config: 配置字典，包含阈值等设置
        """
        self.i18n = get_i18n_manager()
        if config:
            self.threshold_gb = config.get('DISK_ALERT_THRESHOLD', 10)
            self.enabled = config.get('DISK_ALERT_ENABLED', True)
            self.download_location = config.get('BOT_DOWNLOAD_LOCATION', BOT_DOWNLOAD_LOCATION)
        else:
            # 从环境变量或配置文件读取
            self.threshold_gb = int(os.environ.get('DISK_ALERT_THRESHOLD', '10'))
            self.enabled = os.environ.get('DISK_ALERT_ENABLED', 'true').lower() == 'true'
            self.download_location = BOT_DOWNLOAD_LOCATION
            
        self.running = False
        self.check_interval = 300  # 5分钟检查一次
        self.last_alert_time = None
        self.alert_cooldown = 3600  # 1小时内不重复告警
        
    def check_disk_space(self) -> Dict:
        """检查磁盘空间
        
        Returns:
            包含磁盘信息的字典
        """
        try:
            disk_usage = psutil.disk_usage(self.download_location)
            free_space_gb = disk_usage.free / (1024**3)
            used_percent = disk_usage.percent
            
            alert_needed = free_space_gb < self.threshold_gb
            
            return {
                'alert_needed': alert_needed,
                'free_space_gb': round(free_space_gb, 2),
                'used_percent': round(used_percent, 2),
                'total_gb': round(disk_usage.total / (1024**3), 2),
                'used_gb': round(disk_usage.used / (1024**3), 2),
                'threshold_gb': self.threshold_gb,
                'location': self.download_location
            }
        except Exception as e:
            error_msg = self.i18n.translate('disk.monitor.check_failed', error=str(e))
            logger.error(error_msg)
            return {
                'alert_needed': False,
                'error': str(e)
            }
            
    def format_alert_message(self, disk_info: Dict, locale: str = 'zh_CN') -> str:
        """格式化告警消息
        
        Args:
            disk_info: 磁盘信息字典
            locale: 语言代码
            
        Returns:
            格式化的告警消息
        """
        title = self.i18n.translate('disk.monitor.format_alert_title', locale=locale)
        location_label = self.i18n.translate('disk.monitor.format_alert_location', 
                                           location=disk_info.get('location', 'N/A'), 
                                           locale=locale)
        free_space_label = self.i18n.translate('disk.monitor.format_alert_free_space', 
                                             free_space=format_storage_size(disk_info.get('free_space_gb', 0)), 
                                             locale=locale)
        usage_label = self.i18n.translate('disk.monitor.format_alert_usage', 
                                        usage=disk_info.get('used_percent', 0), 
                                        locale=locale)
        threshold_label = self.i18n.translate('disk.monitor.format_alert_threshold', 
                                            threshold=format_storage_size(disk_info.get('threshold_gb', 10)), 
                                            locale=locale)
        action_prompt = self.i18n.translate('disk.monitor.format_alert_action', locale=locale)
        
        message = (
            f"{title} ⚠️\n\n"
            f"{location_label}\n"
            f"{free_space_label}\n"
            f"{usage_label}\n"
            f"{threshold_label}\n\n"
            f"{action_prompt}"
        )
        return message
        
    async def check_and_alert(self) -> Optional[Dict]:
        """检查磁盘并在需要时发送告警
        
        Returns:
            如果需要告警返回磁盘信息，否则返回None
        """
        if not self.enabled:
            return None
            
        disk_info = self.check_disk_space()
        
        if disk_info.get('alert_needed'):
            # 检查是否在冷却期内
            current_time = datetime.now()
            if self.last_alert_time:
                time_diff = (current_time - self.last_alert_time).total_seconds()
                if time_diff < self.alert_cooldown:
                    cooldown_msg = self.i18n.translate('disk.monitor.cooldown_skip', 
                                                     seconds=self.alert_cooldown - time_diff)
                    logger.debug(cooldown_msg)
                    return None
                    
            self.last_alert_time = current_time
            logger.warning(f"磁盘空间不足: {disk_info}")
            return disk_info
            
        return None
        
    async def start_monitoring(self):
        """启动监控循环"""
        self.running = True
        start_msg = self.i18n.translate('disk.monitor.service_started', 
                                       threshold=self.threshold_gb, 
                                       interval=self.check_interval)
        logger.info(start_msg)
        
        while self.running:
            try:
                alert_info = await self.check_and_alert()
                if alert_info:
                    # 这里将触发告警处理器
                    from module.disk.handlers.alert_handler import DiskAlertHandler
                    # 告警处理逻辑将在handler中实现
                    pass
                    
            except Exception as e:
                error_msg = self.i18n.translate('disk.monitor.service_error', error=str(e))
                logger.error(error_msg)
                
            await asyncio.sleep(self.check_interval)
            
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        stop_msg = self.i18n.translate('disk.monitor.service_stopped')
        logger.info(stop_msg)
        
    def reset_alert_cooldown(self):
        """重置告警冷却时间"""
        self.last_alert_time = None
        reset_msg = self.i18n.translate('disk.monitor.cooldown_reset')
        logger.debug(reset_msg)