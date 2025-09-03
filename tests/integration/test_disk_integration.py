"""磁盘监控模块集成测试"""
import asyncio
import unittest
from unittest.mock import patch, Mock
import os
import tempfile
import shutil
from datetime import datetime


class TestDiskMonitorIntegration(unittest.TestCase):
    """磁盘监控集成测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时测试目录
        self.test_dir = tempfile.mkdtemp(prefix='disk_test_')
        self.config = {
            'BOT_DOWNLOAD_LOCATION': self.test_dir,
            'DISK_ALERT_THRESHOLD': 10,
            'DISK_ALERT_ENABLED': True
        }
        
    def tearDown(self):
        """清理测试环境"""
        # 删除测试目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def test_disk_monitor_service_integration(self):
        """测试磁盘监控服务集成"""
        from module.disk.services.disk_monitor import DiskMonitorService
        
        monitor = DiskMonitorService(self.config)
        
        # 检查磁盘空间
        result = monitor.check_disk_space()
        
        # 验证返回结果
        self.assertIn('alert_needed', result)
        self.assertIn('free_space_gb', result)
        self.assertIn('used_percent', result)
        self.assertIn('location', result)
        
        # 验证位置正确
        self.assertEqual(result['location'], self.test_dir)
        
    def test_cleanup_service_integration(self):
        """测试清理服务集成"""
        from module.disk.services.cleanup_service import CleanupService
        
        # 创建测试文件
        test_files = []
        for i in range(5):
            test_file = os.path.join(self.test_dir, f'test_file_{i}.txt')
            with open(test_file, 'w') as f:
                f.write('test content' * 1000)
            test_files.append(test_file)
            
        # 创建测试目录
        test_subdir = os.path.join(self.test_dir, 'test_subdir')
        os.makedirs(test_subdir)
        with open(os.path.join(test_subdir, 'subfile.txt'), 'w') as f:
            f.write('subdir content')
            
        # 初始化清理服务
        cleanup = CleanupService(self.config)
        
        # 获取目录信息
        async def test_get_info():
            return await cleanup.get_directory_info()
            
        dir_info = asyncio.run(test_get_info())
        
        # 验证文件统计
        self.assertTrue(dir_info['exists'])
        self.assertEqual(dir_info['file_count'], 6)  # 5个文件 + 1个子目录文件
        self.assertEqual(dir_info['dir_count'], 1)   # 1个子目录
        
        # 测试清理功能
        async def test_cleanup():
            return await cleanup.clean_download_directory()
            
        result = asyncio.run(test_cleanup())
        
        # 验证清理结果
        self.assertTrue(result['success'])
        self.assertIn('freed_space_gb', result)
        
        # 验证目录已清空
        remaining_files = os.listdir(self.test_dir)
        self.assertEqual(len(remaining_files), 0)
        
    @patch('module.disk.models.disk_alert.DiskAlert.save')
    def test_alert_persistence(self, mock_save):
        """测试告警持久化"""
        from module.disk.models.disk_alert import DiskAlert
        
        # 创建告警记录
        alert = DiskAlert(
            timestamp=datetime.now(),
            free_space_gb=5,
            used_percent=95.0,
            threshold_gb=10,
            alert_message='测试告警',
            alert_status='active'
        )
        
        # 验证字段设置正确
        self.assertEqual(alert.alert_status, 'active')
        self.assertEqual(alert.free_space_gb, 5)
        
        # 解决告警
        alert.resolve(
            action='cleaned_downloads',
            user_id=123456,
            notes='测试清理'
        )
        
        # 验证状态更新
        self.assertEqual(alert.alert_status, 'resolved')
        self.assertEqual(alert.action_taken, 'cleaned_downloads')
        self.assertEqual(alert.resolved_by, 123456)
        self.assertIsNotNone(alert.resolved_at)
        
    def test_celery_adjustment_service(self):
        """测试Celery调整服务"""
        from module.disk.services.celery_adjustment import CeleryAdjustmentService
        
        service = CeleryAdjustmentService()
        
        # 测试获取worker设置
        settings = service.get_current_worker_settings()
        self.assertIsInstance(settings, dict)
        
        # 测试降低频率
        result = service.adjust_worker_frequency('reduce')
        self.assertTrue(result['success'])
        self.assertTrue(service.is_reduced)
        
        # 测试重复降低
        result = service.adjust_worker_frequency('reduce')
        self.assertFalse(result['success'])
        
        # 测试恢复频率
        result = service.adjust_worker_frequency('restore')
        self.assertTrue(result['success'])
        self.assertFalse(service.is_reduced)
        
    async def test_monitor_check_and_alert(self):
        """测试监控检查和告警流程"""
        from module.disk.services.disk_monitor import DiskMonitorService
        
        monitor = DiskMonitorService(self.config)
        
        # 第一次检查（模拟空间不足）
        with patch.object(monitor, 'check_disk_space') as mock_check:
            mock_check.return_value = {
                'alert_needed': True,
                'free_space_gb': 5,
                'used_percent': 95.0,
                'threshold_gb': 10
            }
            
            alert_info = await monitor.check_and_alert()
            self.assertIsNotNone(alert_info)
            self.assertEqual(alert_info['free_space_gb'], 5)
            
        # 第二次立即检查（应该在冷却期内）
        with patch.object(monitor, 'check_disk_space') as mock_check:
            mock_check.return_value = {
                'alert_needed': True,
                'free_space_gb': 5,
                'used_percent': 95.0,
                'threshold_gb': 10
            }
            
            alert_info = await monitor.check_and_alert()
            self.assertIsNone(alert_info)  # 冷却期内不应该返回告警
            
        # 重置冷却时间
        monitor.reset_alert_cooldown()
        
        # 第三次检查（冷却时间已重置）
        with patch.object(monitor, 'check_disk_space') as mock_check:
            mock_check.return_value = {
                'alert_needed': True,
                'free_space_gb': 5,
                'used_percent': 95.0,
                'threshold_gb': 10
            }
            
            alert_info = await monitor.check_and_alert()
            self.assertIsNotNone(alert_info)  # 应该返回告警


if __name__ == '__main__':
    unittest.main()