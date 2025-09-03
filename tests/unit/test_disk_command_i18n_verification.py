"""
TDD 绿灯阶段：验证磁盘命令国际化修复

验证修复后的代码能正确使用i18n翻译系统
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestDiskCommandI18nVerification(unittest.TestCase):
    """TDD 绿灯阶段：磁盘命令国际化修复验证"""
    
    async def test_disk_start_monitor_uses_i18n_successfully(self):
        """
        绿灯测试：启动磁盘监控命令成功使用i18n翻译
        """
        from module.disk.commands.disk_monitor import start_disk_monitor
        
        # Mock Pyrogram 对象
        mock_client = AsyncMock()
        mock_message = AsyncMock()
        mock_message.from_user.id = 12345
        mock_message.reply_text = AsyncMock()
        
        # Mock 相关服务
        with patch('module.disk.commands.disk_monitor.get_global_monitor_service') as mock_global_service:
            with patch('module.disk.commands.disk_monitor.DiskMonitorService') as mock_disk_service:
                # 设置没有运行的监控服务
                mock_global_service.return_value = None
                
                # Mock 磁盘监控服务
                mock_disk_instance = mock_disk_service.return_value
                mock_disk_instance.threshold_gb = 10
                mock_disk_instance.check_interval = 30
                
                # Mock i18n 管理器
                with patch('module.disk.commands.disk_monitor.get_i18n_manager') as mock_get_i18n:
                    mock_i18n = AsyncMock()
                    mock_get_i18n.return_value = mock_i18n
                    
                    # 配置翻译返回值
                    mock_i18n.translate_for_user.side_effect = [
                        "Disk monitor started",  # disk.monitor.started
                        "Monitor Location",      # disk.status.location
                        "Processing..."          # common.loading
                    ]
                    
                    # 执行命令
                    await start_disk_monitor(mock_client, mock_message)
                    
                    # 验证：i18n 管理器被获取
                    mock_get_i18n.assert_called_once()
                    
                    # 验证：调用了翻译方法
                    self.assertGreaterEqual(mock_i18n.translate_for_user.call_count, 3)
                    
                    # 验证：翻译调用包含了正确的用户ID和翻译键
                    calls = mock_i18n.translate_for_user.call_args_list
                    user_id_calls = [call[0][0] for call in calls]
                    self.assertTrue(all(uid == 12345 for uid in user_id_calls))
                    
                    # 验证：使用了正确的翻译键
                    translation_keys = [call[0][1] for call in calls]
                    expected_keys = ['disk.monitor.started', 'disk.status.location']
                    self.assertTrue(any(key in expected_keys for key in translation_keys))
                    
                    # 验证：发送了翻译后的消息
                    mock_message.reply_text.assert_called_once()
                    sent_message = mock_message.reply_text.call_args[0][0]
                    
                    # 验证：消息包含翻译内容
                    self.assertIn("Disk monitor started", sent_message)
    
    async def test_disk_stop_monitor_uses_i18n_successfully(self):
        """
        绿灯测试：停止磁盘监控命令成功使用i18n翻译
        """
        from module.disk.commands.disk_monitor import stop_disk_monitor
        
        # Mock Pyrogram 对象
        mock_client = AsyncMock()
        mock_message = AsyncMock()
        mock_message.from_user.id = 12345
        mock_message.reply_text = AsyncMock()
        
        # Mock 运行中的监控服务
        with patch('module.disk.commands.disk_monitor.get_global_monitor_service') as mock_global_service:
            mock_running_service = MagicMock()
            mock_running_service.running = True
            mock_global_service.return_value = mock_running_service
            
            # Mock i18n 管理器
            with patch('module.disk.commands.disk_monitor.get_i18n_manager') as mock_get_i18n:
                mock_i18n = AsyncMock()
                mock_get_i18n.return_value = mock_i18n
                mock_i18n.translate_for_user.return_value = "Disk monitor stopped"
                
                # 执行命令
                await stop_disk_monitor(mock_client, mock_message)
                
                # 验证：使用了i18n翻译
                mock_i18n.translate_for_user.assert_called_with(12345, 'disk.monitor.stopped')
                
                # 验证：发送了翻译后的消息
                mock_message.reply_text.assert_called_once()
                sent_message = mock_message.reply_text.call_args[0][0]
                self.assertIn("Disk monitor stopped", sent_message)
    
    async def test_disk_help_command_uses_i18n_successfully(self):
        """
        绿灯测试：磁盘帮助命令成功使用i18n翻译
        """
        from module.disk.commands.disk_monitor import show_disk_help
        
        # Mock Message 对象
        mock_message = AsyncMock()
        mock_message.from_user.id = 12345
        mock_message.reply_text = AsyncMock()
        
        # Mock i18n 管理器
        with patch('module.disk.commands.disk_monitor.get_i18n_manager') as mock_get_i18n:
            mock_i18n = AsyncMock()
            mock_get_i18n.return_value = mock_i18n
            mock_i18n.translate_for_user.return_value = """
<b>💿 Disk Management Commands</b>

<b>Available subcommands:</b>
• <code>/disk status</code> - View disk space status
• <code>/disk start</code> - Start disk monitoring
• <code>/disk stop</code> - Stop disk monitoring
• <code>/disk clean</code> - Clean download directory

<b>📱 Click buttons below for quick actions:</b>
"""
            
            # 执行帮助命令
            await show_disk_help(mock_message)
            
            # 验证：使用了i18n翻译
            mock_i18n.translate_for_user.assert_called_with(12345, 'disk.commands.help')
            
            # 验证：发送了翻译后的消息
            mock_message.reply_text.assert_called_once()
            sent_message = mock_message.reply_text.call_args[0][0]
            
            # 验证：消息包含英文内容（而不是硬编码中文）
            self.assertIn("Disk Management Commands", sent_message)
            self.assertIn("Available subcommands", sent_message)
    
    async def test_disk_clean_uses_i18n_successfully(self):
        """
        绿灯测试：磁盘清理命令成功使用i18n翻译
        """
        from module.disk.commands.disk_monitor import disk_clean
        
        # Mock Pyrogram 对象
        mock_client = AsyncMock()
        mock_message = AsyncMock()
        mock_message.from_user.id = 12345
        mock_message.reply_text = AsyncMock()
        
        # Mock 清理服务
        with patch('module.disk.commands.disk_monitor.CleanupService') as mock_cleanup_service:
            mock_cleanup_instance = mock_cleanup_service.return_value
            
            # Mock 清理前后的状态
            mock_cleanup_instance.get_directory_info = AsyncMock(side_effect=[
                # 清理前
                {'file_count': 100, 'total_size_gb': 10.0},
                # 清理后
                {'file_count': 50, 'total_size_gb': 5.0}
            ])
            
            # Mock 成功的清理结果
            mock_cleanup_instance.clean_download_directory = AsyncMock(return_value={
                'success': True,
                'freed_space_gb': 5.0,
                'message': 'Cleanup completed'
            })
            
            # Mock i18n 管理器
            with patch('module.disk.commands.disk_monitor.get_i18n_manager') as mock_get_i18n:
                mock_i18n = AsyncMock()
                mock_get_i18n.return_value = mock_i18n
                
                # 配置翻译返回值
                mock_i18n.translate_for_user.side_effect = [
                    "Cleaning download directory...",  # disk.clean.start
                    "Disk cleanup complete",           # disk.clean.complete
                    "Total freed space"                # disk.clean.freed_space
                ]
                
                # 执行清理命令
                await disk_clean(mock_client, mock_message)
                
                # 验证：调用了多次翻译
                self.assertGreaterEqual(mock_i18n.translate_for_user.call_count, 3)
                
                # 验证：使用了正确的翻译键
                calls = mock_i18n.translate_for_user.call_args_list
                translation_keys = [call[0][1] for call in calls]
                
                expected_keys = ['disk.clean.start', 'disk.clean.complete', 'disk.clean.freed_space']
                for key in expected_keys:
                    self.assertIn(key, translation_keys)
                
                # 验证：发送了两次消息（开始 + 完成）
                self.assertEqual(mock_message.reply_text.call_count, 2)
    
    def test_i18n_import_successful(self):
        """
        绿灯测试：验证i18n导入成功
        """
        # 验证：可以成功导入i18n相关模块
        from module.disk.commands.disk_monitor import get_i18n_manager
        self.assertIsNotNone(get_i18n_manager)
        
        # 验证：可以获取i18n管理器实例
        i18n_manager = get_i18n_manager()
        self.assertIsNotNone(i18n_manager)
        
        # 验证：i18n管理器有翻译方法
        self.assertTrue(hasattr(i18n_manager, 'translate_for_user'))
    
    async def test_user_language_is_correctly_obtained_in_commands(self):
        """
        绿灯测试：命令中正确获取用户语言
        """
        from module.disk.commands.disk_monitor import start_disk_monitor
        
        # Mock Pyrogram 对象
        mock_client = AsyncMock()
        mock_message = AsyncMock()
        mock_message.from_user.id = 67890  # 不同的用户ID
        mock_message.reply_text = AsyncMock()
        
        # Mock 相关服务
        with patch('module.disk.commands.disk_monitor.get_global_monitor_service') as mock_global_service:
            with patch('module.disk.commands.disk_monitor.DiskMonitorService') as mock_disk_service:
                mock_global_service.return_value = None
                mock_disk_instance = mock_disk_service.return_value
                mock_disk_instance.threshold_gb = 10
                mock_disk_instance.check_interval = 30
                
                # Mock i18n 管理器
                with patch('module.disk.commands.disk_monitor.get_i18n_manager') as mock_get_i18n:
                    mock_i18n = AsyncMock()
                    mock_get_i18n.return_value = mock_i18n
                    mock_i18n.translate_for_user.return_value = "Test message"
                    
                    # 执行命令
                    await start_disk_monitor(mock_client, mock_message)
                    
                    # 验证：所有翻译调用都使用了正确的用户ID
                    calls = mock_i18n.translate_for_user.call_args_list
                    user_ids = [call[0][0] for call in calls]
                    
                    # 验证：所有调用都使用了消息中的用户ID
                    self.assertTrue(all(uid == 67890 for uid in user_ids))


if __name__ == '__main__':
    print("=" * 70)
    print("TDD 绿灯阶段 - 磁盘命令国际化修复验证测试")
    print("=" * 70)
    print("验证修复效果：")
    print("1. 磁盘命令成功集成i18n翻译系统")
    print("2. 不同命令都正确使用翻译键")
    print("3. 用户语言被正确获取和传递")
    print("=" * 70)
    
    async def run_verification_tests():
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestDiskCommandI18nVerification)
        
        passed = 0
        failed = 0
        
        for test in suite:
            test_method = getattr(test, test._testMethodName)
            if asyncio.iscoroutinefunction(test_method):
                try:
                    await test_method(test)
                    print(f"🟢 {test._testMethodName} - 通过")
                    passed += 1
                except AssertionError as e:
                    print(f"🔴 {test._testMethodName} - 失败: {str(e)[:80]}...")
                    failed += 1
                except Exception as e:
                    print(f"❌ {test._testMethodName} - 错误: {str(e)[:80]}...")
                    failed += 1
            else:
                try:
                    test_method(test)
                    print(f"🟢 {test._testMethodName} - 通过")
                    passed += 1
                except AssertionError as e:
                    print(f"🔴 {test._testMethodName} - 失败: {str(e)[:80]}...")
                    failed += 1
                except Exception as e:
                    print(f"❌ {test._testMethodName} - 错误: {str(e)[:80]}...")
                    failed += 1
        
        print("=" * 70)
        print(f"绿灯阶段结果：通过 {passed}，失败 {failed}")
        if failed == 0:
            print("🎉 所有验证测试通过！磁盘命令国际化已成功修复！")
        else:
            print("⚠️ 部分测试失败，需要进一步修复")
        print("=" * 70)
    
    asyncio.run(run_verification_tests())