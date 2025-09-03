"""
网络监控服务
提供网络接口统计和实时带宽监控功能
"""

import time
import asyncio
import psutil
from datetime import datetime
from typing import Dict, Optional, List
from loguru import logger
from module.network.utils.format_utils import format_bandwidth, format_data_size
from module.i18n.services.i18n_manager import I18nManager

# 初始化国际化管理器
i18n_manager = I18nManager()


class NetworkMonitorService:
    """网络监控服务"""
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化网络监控服务
        
        Args:
            config: 配置字典
        """
        self.running = False
        self.check_interval = 2  # 2秒检查一次用于实时带宽计算
        self.last_stats = None
        self.last_check_time = None
        
        # 带宽监控历史数据
        self.bandwidth_history = []
        self.max_history_size = 30  # 保存最近30个数据点
        
    def get_network_interfaces(self) -> List[str]:
        """获取所有网络接口名称
        
        Returns:
            网络接口名称列表
        """
        try:
            stats = psutil.net_io_counters(pernic=True)
            return list(stats.keys())
        except Exception as e:
            logger.error(f"{i18n_manager.translate('network.monitor.get_interfaces_failed', 'zh_CN', error=str(e))}")
            return []
    
    def get_network_stats(self, interface: Optional[str] = None) -> Dict:
        """获取网络统计信息
        
        Args:
            interface: 指定网络接口，None则获取总计
            
        Returns:
            包含网络统计的字典
        """
        try:
            if interface:
                stats = psutil.net_io_counters(pernic=True).get(interface)
                if not stats:
                    return {'error': i18n_manager.translate('network.monitor.interface_not_found', 'zh_CN', interface=interface)}
            else:
                stats = psutil.net_io_counters()
                
            current_time = time.time()
            
            network_info = {
                'interface': interface or 'Total',
                'bytes_sent': stats.bytes_sent,
                'bytes_recv': stats.bytes_recv,
                'packets_sent': stats.packets_sent,
                'packets_recv': stats.packets_recv,
                'errin': stats.errin,
                'errout': stats.errout,
                'dropin': stats.dropin,
                'dropout': stats.dropout,
                'timestamp': current_time
            }
            
            # 计算实时带宽
            if self.last_stats and self.last_check_time:
                time_diff = current_time - self.last_check_time
                if time_diff > 0:
                    sent_speed = (stats.bytes_sent - self.last_stats.bytes_sent) / time_diff
                    recv_speed = (stats.bytes_recv - self.last_stats.bytes_recv) / time_diff
                    
                    network_info['upload_speed'] = max(0, sent_speed)
                    network_info['download_speed'] = max(0, recv_speed)
                    network_info['total_speed'] = network_info['upload_speed'] + network_info['download_speed']
                    
                    # 更新带宽历史
                    bandwidth_data = {
                        'timestamp': current_time,
                        'upload': network_info['upload_speed'],
                        'download': network_info['download_speed']
                    }
                    
                    self.bandwidth_history.append(bandwidth_data)
                    if len(self.bandwidth_history) > self.max_history_size:
                        self.bandwidth_history.pop(0)
                else:
                    network_info['upload_speed'] = 0
                    network_info['download_speed'] = 0
                    network_info['total_speed'] = 0
            else:
                network_info['upload_speed'] = 0
                network_info['download_speed'] = 0
                network_info['total_speed'] = 0
                
            # 更新上次检查数据
            self.last_stats = stats
            self.last_check_time = current_time
            
            return network_info
            
        except Exception as e:
            logger.error(f"{i18n_manager.translate('network.monitor.get_stats_failed', 'zh_CN', error=str(e))}")
            return {
                'error': str(e),
                'interface': interface or 'Total'
            }
    
    def get_connection_stats(self) -> Dict:
        """获取网络连接统计
        
        Returns:
            包含连接统计的字典
        """
        try:
            connections = psutil.net_connections()
            
            stats = {
                'total_connections': len(connections),
                'tcp_connections': 0,
                'udp_connections': 0,
                'listening_ports': 0,
                'established_connections': 0,
                'time_wait_connections': 0
            }
            
            for conn in connections:
                if conn.type == 1:  # TCP
                    stats['tcp_connections'] += 1
                    if conn.status == 'LISTEN':
                        stats['listening_ports'] += 1
                    elif conn.status == 'ESTABLISHED':
                        stats['established_connections'] += 1
                    elif conn.status == 'TIME_WAIT':
                        stats['time_wait_connections'] += 1
                elif conn.type == 2:  # UDP
                    stats['udp_connections'] += 1
                    
            return stats
            
        except Exception as e:
            logger.error(f"{i18n_manager.translate('network.monitor.get_connections_failed', 'zh_CN', error=str(e))}")
            return {'error': str(e)}
    
    def get_bandwidth_average(self, minutes: int = 5) -> Dict:
        """获取指定时间内的平均带宽
        
        Args:
            minutes: 时间窗口(分钟)
            
        Returns:
            包含平均带宽的字典
        """
        if not self.bandwidth_history:
            return {
                'avg_upload': 0,
                'avg_download': 0,
                'avg_total': 0,
                'data_points': 0
            }
        
        cutoff_time = time.time() - (minutes * 60)
        recent_data = [data for data in self.bandwidth_history if data['timestamp'] > cutoff_time]
        
        if not recent_data:
            return {
                'avg_upload': 0,
                'avg_download': 0,
                'avg_total': 0,
                'data_points': 0
            }
        
        avg_upload = sum(data['upload'] for data in recent_data) / len(recent_data)
        avg_download = sum(data['download'] for data in recent_data) / len(recent_data)
        
        return {
            'avg_upload': avg_upload,
            'avg_download': avg_download,
            'avg_total': avg_upload + avg_download,
            'data_points': len(recent_data)
        }
    
    def get_peak_bandwidth(self) -> Dict:
        """获取峰值带宽
        
        Returns:
            包含峰值带宽的字典
        """
        if not self.bandwidth_history:
            return {
                'peak_upload': 0,
                'peak_download': 0,
                'peak_total': 0
            }
        
        peak_upload = max(data['upload'] for data in self.bandwidth_history)
        peak_download = max(data['download'] for data in self.bandwidth_history)
        peak_total = max(data['upload'] + data['download'] for data in self.bandwidth_history)
        
        return {
            'peak_upload': peak_upload,
            'peak_download': peak_download,
            'peak_total': peak_total
        }
    
    async def start_monitoring(self):
        """启动监控循环"""
        self.running = True
        logger.info(f"{i18n_manager.translate('network.monitor.service_started', 'zh_CN', interval=self.check_interval)}")
        
        while self.running:
            try:
                # 更新网络统计以计算实时带宽
                self.get_network_stats()
                
            except Exception as e:
                logger.error(f"{i18n_manager.translate('network.monitor.service_error', 'zh_CN', error=str(e))}")
                
            await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        logger.info(f"{i18n_manager.translate('network.monitor.service_stopped', 'zh_CN')}")
        
    def reset_history(self):
        """重置带宽历史数据"""
        self.bandwidth_history = []
        self.last_stats = None
        self.last_check_time = None
        logger.debug(f"{i18n_manager.translate('network.monitor.history_reset', 'zh_CN')}")