import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from datetime import datetime
import psutil


class TestDiskMonitorService(unittest.TestCase):
    """磁盘监控服务单元测试"""
    
    def setUp(self):
        """测试前初始化"""
        self.mock_config = {
            'DISK_ALERT_THRESHOLD': 10,  # 10GB
            'DISK_ALERT_ENABLED': True,
            'BOT_DOWNLOAD_LOCATION': '/tmp/downloads'
        }
        
    @patch('module.disk.services.disk_monitor.psutil.disk_usage')
    def test_check_disk_space_normal(self, mock_disk_usage):
        """测试磁盘空间正常情况"""
        # 模拟磁盘空间充足
        mock_disk_usage.return_value = Mock(
            total=100 * 1024**3,  # 100GB
            used=50 * 1024**3,     # 50GB
            free=50 * 1024**3,     # 50GB
            percent=50.0
        )
        
        from module.disk.services.disk_monitor import DiskMonitorService
        monitor = DiskMonitorService(self.mock_config)
        
        result = monitor.check_disk_space()
        self.assertFalse(result['alert_needed'])
        self.assertEqual(result['free_space_gb'], 50)
        self.assertEqual(result['used_percent'], 50.0)
        
    @patch('module.disk.services.disk_monitor.psutil.disk_usage')
    def test_check_disk_space_alert(self, mock_disk_usage):
        """测试磁盘空间不足触发告警"""
        # 模拟磁盘空间不足
        mock_disk_usage.return_value = Mock(
            total=100 * 1024**3,  # 100GB
            used=95 * 1024**3,    # 95GB
            free=5 * 1024**3,     # 5GB
            percent=95.0
        )
        
        from module.disk.services.disk_monitor import DiskMonitorService
        monitor = DiskMonitorService(self.mock_config)
        
        result = monitor.check_disk_space()
        self.assertTrue(result['alert_needed'])
        self.assertEqual(result['free_space_gb'], 5)
        self.assertEqual(result['used_percent'], 95.0)
        
    def test_format_alert_message(self):
        """测试格式化告警消息"""
        from module.disk.services.disk_monitor import DiskMonitorService
        monitor = DiskMonitorService(self.mock_config)
        
        disk_info = {
            'free_space_gb': 5,
            'used_percent': 95.0,
            'threshold_gb': 10
        }
        
        message = monitor.format_alert_message(disk_info)
        self.assertIn('磁盘空间告警', message)
        self.assertIn('5.00GB', message)  # 更新为格式化后的值
        self.assertIn('95.0%', message)
        
    @patch('module.disk.services.disk_monitor.asyncio.sleep')
    async def test_start_monitoring(self, mock_sleep):
        """测试启动监控循环"""
        from module.disk.services.disk_monitor import DiskMonitorService
        monitor = DiskMonitorService(self.mock_config)
        
        # 模拟运行3次后停止
        monitor.running = True
        call_count = 0
        
        async def side_effect(delay):
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                monitor.running = False
            return
            
        mock_sleep.side_effect = side_effect
        
        with patch.object(monitor, 'check_and_alert', new_callable=AsyncMock) as mock_check:
            await monitor.start_monitoring()
            self.assertEqual(mock_check.call_count, 3)


class TestDiskAlertModel(unittest.TestCase):
    """磁盘告警MongoDB模型测试"""
    
    @patch('mongoengine.connect')
    def test_create_alert_record(self, mock_connect):
        """测试创建告警记录"""
        from module.disk.models.disk_alert import DiskAlert
        
        alert = DiskAlert(
            timestamp=datetime.now(),
            free_space_gb=5,
            used_percent=95.0,
            threshold_gb=10,
            alert_message='磁盘空间不足',
            alert_status='active',
            action_taken=None
        )
        
        # 验证字段
        self.assertEqual(alert.free_space_gb, 5)
        self.assertEqual(alert.used_percent, 95.0)
        self.assertEqual(alert.alert_status, 'active')
        self.assertIsNone(alert.action_taken)
        
    @patch('mongoengine.connect')
    def test_update_alert_status(self, mock_connect):
        """测试更新告警状态"""
        from module.disk.models.disk_alert import DiskAlert
        
        alert = DiskAlert(
            timestamp=datetime.now(),
            free_space_gb=5,
            used_percent=95.0,
            threshold_gb=10,
            alert_message='磁盘空间不足',
            alert_status='active'
        )
        
        # 更新状态
        alert.alert_status = 'resolved'
        alert.action_taken = 'cleaned_downloads'
        alert.resolved_at = datetime.now()
        
        self.assertEqual(alert.alert_status, 'resolved')
        self.assertEqual(alert.action_taken, 'cleaned_downloads')
        self.assertIsNotNone(alert.resolved_at)


class TestDiskCleanupService(unittest.TestCase):
    """磁盘清理服务测试"""
    
    def setUp(self):
        self.mock_config = {
            'BOT_DOWNLOAD_LOCATION': '/tmp/downloads'
        }
        
    @patch('os.listdir')
    @patch('os.path.getsize')
    def test_calculate_directory_size(self, mock_getsize, mock_listdir):
        """测试计算目录大小"""
        mock_listdir.return_value = ['file1.mp4', 'file2.mp4', 'file3.mp4']
        mock_getsize.side_effect = [
            1024 * 1024 * 100,  # 100MB
            1024 * 1024 * 200,  # 200MB
            1024 * 1024 * 300,  # 300MB
        ]
        
        from module.disk.services.cleanup_service import CleanupService
        service = CleanupService(self.mock_config)
        
        total_size = service.calculate_directory_size('/tmp/downloads')
        self.assertEqual(total_size, 1024 * 1024 * 600)  # 600MB
        
    @patch('shutil.rmtree')
    @patch('os.path.exists')
    @patch('os.makedirs')
    async def test_clean_download_directory(self, mock_makedirs, mock_exists, mock_rmtree):
        """测试清空下载目录"""
        mock_exists.return_value = True
        
        from module.disk.services.cleanup_service import CleanupService
        service = CleanupService(self.mock_config)
        
        result = await service.clean_download_directory()
        
        self.assertTrue(result['success'])
        mock_rmtree.assert_called_once_with('/tmp/downloads')
        mock_makedirs.assert_called_once_with('/tmp/downloads', exist_ok=True)
        
    @patch('os.path.exists')
    async def test_clean_download_directory_not_exists(self, mock_exists):
        """测试清空不存在的目录"""
        mock_exists.return_value = False
        
        from module.disk.services.cleanup_service import CleanupService
        service = CleanupService(self.mock_config)
        
        result = await service.clean_download_directory()
        
        self.assertFalse(result['success'])
        self.assertIn('不存在', result['message'])


class TestCeleryAdjustmentService(unittest.TestCase):
    """Celery频率调整服务测试"""
    
    @patch('tool.celery_client.celery_app')
    def test_get_current_worker_settings(self, mock_celery):
        """测试获取当前worker设置"""
        from module.disk.services.celery_adjustment import CeleryAdjustmentService
        
        mock_celery.control.inspect.return_value.active.return_value = {
            'worker1': [],
            'worker2': []
        }
        
        service = CeleryAdjustmentService()
        workers = service.get_current_worker_settings()
        
        self.assertEqual(len(workers), 2)
        self.assertIn('worker1', workers)
        
    @patch('tool.celery_client.celery_app')
    def test_adjust_worker_frequency(self, mock_celery):
        """测试调整worker频率"""
        from module.disk.services.celery_adjustment import CeleryAdjustmentService
        
        service = CeleryAdjustmentService()
        
        # 测试降低频率
        result = service.adjust_worker_frequency('reduce')
        self.assertTrue(result['success'])
        
        # 测试恢复频率
        result = service.adjust_worker_frequency('restore')
        self.assertTrue(result['success'])
        
    @patch('tool.celery_client.celery_app')
    def test_pause_resume_workers(self, mock_celery):
        """测试暂停和恢复workers"""
        from module.disk.services.celery_adjustment import CeleryAdjustmentService
        
        service = CeleryAdjustmentService()
        
        # 测试暂停
        result = service.pause_workers()
        self.assertTrue(result['success'])
        mock_celery.control.pause.assert_called_once()
        
        # 测试恢复
        result = service.resume_workers()
        self.assertTrue(result['success'])
        mock_celery.control.resume.assert_called_once()


class TestDiskAlertHandler(unittest.TestCase):
    """磁盘告警处理器测试"""
    
    def setUp(self):
        self.mock_bot = AsyncMock()
        self.mock_message = Mock()
        self.mock_callback_query = Mock()
        
    async def test_send_alert_with_buttons(self):
        """测试发送带按钮的告警消息"""
        from module.disk.handlers.alert_handler import DiskAlertHandler
        
        handler = DiskAlertHandler(self.mock_bot)
        
        alert_info = {
            'free_space_gb': 5,
            'used_percent': 95.0,
            'threshold_gb': 10
        }
        
        await handler.send_alert_with_buttons(123456, alert_info)
        
        # 验证调用了发送消息
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args
        
        # 验证消息内容
        self.assertIn('磁盘空间告警', call_args[1]['text'])
        
        # 验证有回调按钮
        self.assertIsNotNone(call_args[1].get('reply_markup'))
        
    async def test_handle_cleanup_callback(self):
        """测试处理清理回调"""
        from module.disk.handlers.alert_handler import DiskAlertHandler
        
        handler = DiskAlertHandler(self.mock_bot)
        
        self.mock_callback_query.data = 'disk_cleanup'
        self.mock_callback_query.message.chat.id = 123456
        
        with patch('module.disk.services.cleanup_service.CleanupService') as MockCleanup:
            mock_service = MockCleanup.return_value
            mock_service.clean_download_directory = AsyncMock(return_value={
                'success': True,
                'freed_space_gb': 20
            })
            
            await handler.handle_callback(self.mock_callback_query)
            
            # 验证调用了清理服务
            mock_service.clean_download_directory.assert_called_once()
            
            # 验证回复了消息
            self.mock_callback_query.answer.assert_called_once()
            
    async def test_handle_adjust_celery_callback(self):
        """测试处理调整Celery回调"""
        from module.disk.handlers.alert_handler import DiskAlertHandler
        
        handler = DiskAlertHandler(self.mock_bot)
        
        self.mock_callback_query.data = 'disk_adjust_celery'
        
        with patch('module.disk.services.celery_adjustment.CeleryAdjustmentService') as MockCelery:
            mock_service = MockCelery.return_value
            mock_service.adjust_worker_frequency = Mock(return_value={
                'success': True,
                'action': 'reduced'
            })
            
            await handler.handle_callback(self.mock_callback_query)
            
            # 验证调用了调整服务
            mock_service.adjust_worker_frequency.assert_called_once()
            
            # 验证回复了消息
            self.mock_callback_query.answer.assert_called_once()


if __name__ == '__main__':
    unittest.main()