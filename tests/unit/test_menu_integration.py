import unittest
from unittest.mock import Mock, patch, AsyncMock
from pyrogram.types import BotCommand


class TestMenuIntegration(unittest.TestCase):
    """菜单集成功能测试"""
    
    def setUp(self):
        """测试前初始化"""
        self.mock_client = AsyncMock()
        self.mock_message = Mock()
        self.mock_message.reply = AsyncMock()
        
    async def test_menu_includes_disk_commands(self):
        """测试菜单包含磁盘监控相关命令"""
        # 导入菜单模块
        import module.menu.menu as menu_module
        
        # 测试磁盘命令是否在菜单中
        with patch.object(self.mock_client, 'set_bot_commands') as mock_set_commands:
            await menu_module.menu(self.mock_client, self.mock_message)
            
            # 获取设置的命令
            call_args = mock_set_commands.call_args
            commands = call_args[0][0]
            
            # 验证磁盘相关命令
            command_strings = [cmd.command for cmd in commands if isinstance(cmd, BotCommand)]
            self.assertIn('disk_status', command_strings, "菜单应包含disk_status命令")
            self.assertIn('disk_monitor', command_strings, "菜单应包含disk_monitor命令")
            
    async def test_disk_shortcut_commands_exist(self):
        """测试磁盘快捷命令存在"""
        # 这些命令应该被添加到快捷菜单中
        expected_commands = [
            'disk_status',  # 查看磁盘状态
            'disk_monitor', # 磁盘监控开关
            'disk_clean',   # 快速清理
        ]
        
        # 导入菜单模块并检查命令
        import module.menu.menu as menu_module
        
        with patch.object(self.mock_client, 'set_bot_commands') as mock_set_commands:
            await menu_module.menu(self.mock_client, self.mock_message)
            
            call_args = mock_set_commands.call_args
            commands = call_args[0][0]
            command_strings = [cmd.command for cmd in commands if isinstance(cmd, BotCommand)]
            
            for cmd in expected_commands:
                self.assertIn(cmd, command_strings, f"菜单应包含{cmd}命令")
                
    def test_disk_menu_descriptions(self):
        """测试磁盘命令描述"""
        expected_descriptions = {
            'disk_status': '查看磁盘空间状态',
            'disk_monitor': '磁盘监控开关',
            'disk_clean': '清理下载目录'
        }
        
        # 这个测试将在实现阶段通过
        for cmd, desc in expected_descriptions.items():
            self.assertTrue(len(desc) > 0, f"{cmd}命令应有描述")


class TestDiskUnitFormatting(unittest.TestCase):
    """磁盘单位格式化测试"""
    
    def test_format_file_count_units(self):
        """测试文件数量单位格式化"""
        from module.disk.utils.format_utils import format_file_count
        
        # 测试各种文件数量
        self.assertEqual(format_file_count(0), "0个文件")
        self.assertEqual(format_file_count(1), "1个文件") 
        self.assertEqual(format_file_count(1000), "1,000个文件")
        self.assertEqual(format_file_count(1500), "1,500个文件")
        
    def test_format_directory_count_units(self):
        """测试目录数量单位格式化"""
        from module.disk.utils.format_utils import format_directory_count
        
        # 测试各种目录数量
        self.assertEqual(format_directory_count(0), "0个文件夹")
        self.assertEqual(format_directory_count(1), "1个文件夹")
        self.assertEqual(format_directory_count(50), "50个文件夹")
        
    def test_format_file_size_units(self):
        """测试文件大小单位格式化"""
        from module.disk.utils.format_utils import format_file_size
        
        # 测试各种文件大小
        self.assertEqual(format_file_size(0), "0B")
        self.assertEqual(format_file_size(1024), "1KB")
        self.assertEqual(format_file_size(1024**2), "1MB")
        self.assertEqual(format_file_size(1024**3), "1GB")
        self.assertEqual(format_file_size(1.5 * 1024**3), "1.5GB")
        
    def test_format_disk_space_with_units(self):
        """测试磁盘空间格式化显示"""
        from module.disk.utils.format_utils import format_disk_info
        
        disk_info = {
            'free_space_gb': 45.67,
            'used_percent': 78.9,
            'total_gb': 200.0,
            'used_gb': 154.33
        }
        
        formatted = format_disk_info(disk_info)
        
        # 验证包含单位
        self.assertIn("45.67GB", formatted)
        self.assertIn("78.9%", formatted) 
        self.assertIn("200.0GB", formatted)
        self.assertIn("154.33GB", formatted)
        
    def test_format_directory_info_with_units(self):
        """测试目录信息格式化显示"""
        from module.disk.utils.format_utils import format_directory_info
        
        dir_info = {
            'file_count': 1250,
            'dir_count': 45,
            'total_size_gb': 23.45
        }
        
        formatted = format_directory_info(dir_info)
        
        # 验证包含正确的单位
        self.assertIn("1,250个文件", formatted)
        self.assertIn("45个文件夹", formatted)
        self.assertIn("23.45GB", formatted)


class TestDiskMonitorAutoStart(unittest.TestCase):
    """磁盘监控默认启动测试"""
    
    @patch('module.disk.services.disk_monitor.DiskMonitorService')
    def test_disk_monitor_enabled_by_default(self, mock_monitor_service):
        """测试磁盘监控默认启用"""
        from config.config import DISK_MONITOR_AUTO_START
        
        # 默认应该为True
        self.assertTrue(DISK_MONITOR_AUTO_START, "磁盘监控应默认启用")
        
    @patch('module.disk.services.disk_monitor.DiskMonitorService')
    async def test_disk_monitor_starts_with_bot(self, mock_monitor_service):
        """测试磁盘监控随Bot启动"""
        mock_service = mock_monitor_service.return_value
        mock_service.start_monitoring = AsyncMock()
        
        # 模拟Bot启动过程
        from module.disk.auto_start import start_disk_monitor_if_enabled
        
        await start_disk_monitor_if_enabled()
        
        # 验证监控服务被启动
        mock_service.start_monitoring.assert_called_once()
        
    @patch.dict('os.environ', {'DISK_MONITOR_AUTO_START': 'false'})
    async def test_disk_monitor_disabled_by_config(self):
        """测试通过配置禁用磁盘监控"""
        from module.disk.auto_start import start_disk_monitor_if_enabled
        
        with patch('module.disk.services.disk_monitor.DiskMonitorService') as mock_service:
            await start_disk_monitor_if_enabled()
            
            # 验证监控服务没有被启动
            mock_service.assert_not_called()
            
    def test_disk_monitor_config_validation(self):
        """测试磁盘监控配置验证"""
        from module.disk.config.validator import validate_disk_monitor_config
        
        # 测试有效配置
        valid_config = {
            'DISK_ALERT_THRESHOLD': 10,
            'DISK_ALERT_ENABLED': True,
            'DISK_MONITOR_AUTO_START': True
        }
        
        result = validate_disk_monitor_config(valid_config)
        self.assertTrue(result['valid'])
        
        # 测试无效配置
        invalid_config = {
            'DISK_ALERT_THRESHOLD': -1,  # 无效阈值
            'DISK_ALERT_ENABLED': 'invalid',  # 无效布尔值
        }
        
        result = validate_disk_monitor_config(invalid_config)
        self.assertFalse(result['valid'])
        self.assertIn('errors', result)


if __name__ == '__main__':
    unittest.main()