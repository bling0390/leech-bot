"""
TDD 红灯阶段：修复磁盘命令国际化问题

问题分析：
1. 用户切换语言为 en_US 后，/disk 命令的消息仍然显示中文
2. disk_monitor.py 中大量硬编码中文字符串
3. 没有使用 i18n 翻译系统

修复目标：确保所有命令消息都支持国际化翻译
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock, call
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestDiskCommandI18nFix(unittest.TestCase):
    """TDD 红灯阶段：磁盘命令国际化修复测试"""
    
    async def test_disk_status_should_use_i18n_translations(self):
        """
        失败测试：/disk status 命令应该使用i18n翻译而不是硬编码中文
        """
        from module.disk.commands.disk_monitor import handle_disk_status
        from module.i18n import get_i18n_manager
        
        # Mock Pyrogram 对象
        mock_client = AsyncMock()
        mock_message = AsyncMock()
        mock_message.from_user.id = 12345
        mock_message.reply_text = AsyncMock()
        
        # Mock 磁盘服务返回值
        with patch('module.disk.commands.disk_monitor.DiskMonitorService') as mock_disk_service:
            with patch('module.disk.commands.disk_monitor.CleanupService') as mock_cleanup_service:
                # Mock 返回值
                mock_disk_instance = mock_disk_service.return_value
                mock_disk_instance.check_disk_space.return_value = {
                    'location': '/test/path',
                    'free_space_gb': 50.0,
                    'used_percent': 60.0,
                    'total_gb': 100.0,
                    'used_gb': 50.0,
                    'alert_needed': False
                }
                
                mock_cleanup_instance = mock_cleanup_service.return_value
                mock_cleanup_instance.get_directory_info = AsyncMock(return_value={
                    'file_count': 100,
                    'dir_count': 10,
                    'total_size_gb': 5.0
                })
                
                # 设置用户语言为 en_US
                with patch('module.i18n.services.i18n_manager.get_user_language') as mock_get_lang:
                    mock_get_lang.return_value = 'en_US'
                    
                    # 执行命令
                    await handle_disk_status(mock_client, mock_message)
                    
                    # 获取发送的消息内容
                    mock_message.reply_text.assert_called_once()
                    sent_message = mock_message.reply_text.call_args[0][0]
                    
                    # 验证：消息不应该包含硬编码的中文
                    chinese_terms = [
                        "磁盘状态报告", "监控位置", "剩余空间", "使用率", "总空间", 
                        "已使用", "下载目录信息", "文件数量", "目录数量", "占用空间",
                        "系统状态", "磁盘空间", "监控服务", "运行中", "未运行"
                    ]
                    
                    for term in chinese_terms:
                        self.assertNotIn(term, sent_message, 
                                       f"消息不应包含硬编码的中文 '{term}'，当前用户语言为 en_US")
                    
                    # 验证：消息应该包含英文翻译
                    expected_english_terms = [
                        "Disk Status Report", "Monitor Location", "Free Space", "Usage",
                        "Total Space", "Used Space", "Directory Info", "File Count", 
                        "Directory Count"
                    ]
                    
                    found_english_terms = 0
                    for term in expected_english_terms:
                        if term in sent_message:
                            found_english_terms += 1
                    
                    # 这个测试会失败，因为当前没有使用i18n翻译
                    self.assertGreater(found_english_terms, 3, 
                                     f"消息应该包含英文翻译内容，但只找到了{found_english_terms}个英文术语")
    
    async def test_disk_start_monitor_should_use_user_language(self):
        """
        失败测试：启动磁盘监控命令应该根据用户语言显示消息
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
                
                # 设置用户语言为 en_US
                with patch('module.i18n.services.i18n_manager.get_user_language') as mock_get_lang:
                    mock_get_lang.return_value = 'en_US'
                    
                    # 执行命令
                    await start_disk_monitor(mock_client, mock_message)
                    
                    # 获取发送的消息内容
                    mock_message.reply_text.assert_called_once()
                    sent_message = mock_message.reply_text.call_args[0][0]
                    
                    # 验证：不应该包含硬编码中文
                    chinese_terms = [
                        "磁盘监控启动成功", "监控配置信息", "监控位置", "告警阈值", 
                        "检查间隔", "已启动", "秒"
                    ]
                    
                    for term in chinese_terms:
                        self.assertNotIn(term, sent_message, 
                                       f"启动监控消息不应包含硬编码中文 '{term}'")
                    
                    # 验证：应该包含英文翻译
                    self.assertIn("started", sent_message.lower(), 
                                "启动监控消息应该包含英文翻译")
    
    async def test_disk_help_command_should_be_translated(self):
        """
        失败测试：磁盘帮助命令应该根据用户语言翻译
        """
        from module.disk.commands.disk_monitor import show_disk_help
        
        # Mock Message 对象
        mock_message = AsyncMock()
        mock_message.from_user.id = 12345
        mock_message.reply_text = AsyncMock()
        
        # 设置用户语言为 en_US
        with patch('module.i18n.services.i18n_manager.get_user_language') as mock_get_lang:
            mock_get_lang.return_value = 'en_US'
            
            # 执行帮助命令
            await show_disk_help(mock_message)
            
            # 获取发送的消息内容和键盘
            mock_message.reply_text.assert_called_once()
            call_args = mock_message.reply_text.call_args
            sent_message = call_args[0][0]
            
            # 验证：不应该包含硬编码中文
            chinese_terms = [
                "磁盘管理命令", "可用子命令", "查看磁盘空间状态", "启动磁盘监控",
                "停止磁盘监控", "清理下载目录", "清理天前的文件", "查看最近告警",
                "示例", "点击下方按钮快速执行命令"
            ]
            
            for term in chinese_terms:
                self.assertNotIn(term, sent_message, 
                               f"帮助消息不应包含硬编码中文 '{term}'，应该使用翻译")
            
            # 验证：应该包含英文翻译的关键内容
            expected_english_content = [
                "Disk Management", "Available subcommands", "status", "start", "stop", "clean"
            ]
            
            english_content_found = 0
            for content in expected_english_content:
                if content.lower() in sent_message.lower():
                    english_content_found += 1
            
            # 这个测试会失败，因为当前帮助内容是硬编码中文
            self.assertGreater(english_content_found, 3,
                             f"帮助消息应该包含英文翻译，但只找到了{english_content_found}个英文内容")
    
    async def test_disk_clean_messages_should_be_internationalized(self):
        """
        失败测试：磁盘清理命令的消息应该国际化
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
            
            # 设置用户语言为 en_US
            with patch('module.i18n.services.i18n_manager.get_user_language') as mock_get_lang:
                mock_get_lang.return_value = 'en_US'
                
                # 执行清理命令
                await disk_clean(mock_client, mock_message)
                
                # 验证两次消息调用：开始清理 + 完成清理
                self.assertEqual(mock_message.reply_text.call_count, 2)
                
                # 获取两个消息
                first_call = mock_message.reply_text.call_args_list[0][0][0]
                second_call = mock_message.reply_text.call_args_list[1][0][0]
                
                # 验证第一个消息（开始清理）不应包含中文
                self.assertNotIn("正在清理下载目录", first_call,
                               "开始清理消息应该翻译为英文")
                
                # 验证第二个消息（完成清理）不应包含中文
                chinese_terms_complete = [
                    "磁盘清理完成", "文件数", "占用空间", "总计释放空间"
                ]
                
                for term in chinese_terms_complete:
                    self.assertNotIn(term, second_call,
                                   f"完成清理消息不应包含硬编码中文 '{term}'")
                
                # 验证：应该包含英文翻译
                self.assertTrue(
                    "cleaning" in first_call.lower() or "processing" in first_call.lower(),
                    "开始清理消息应该包含英文翻译"
                )
                
                self.assertTrue(
                    "complete" in second_call.lower() or "finished" in second_call.lower(),
                    "完成清理消息应该包含英文翻译"
                )
    
    async def test_disk_already_running_message_should_be_translated(self):
        """
        失败测试：监控已运行的消息应该翻译
        """
        from module.disk.commands.disk_monitor import start_disk_monitor
        
        # Mock Pyrogram 对象
        mock_client = AsyncMock()
        mock_message = AsyncMock()
        mock_message.from_user.id = 12345
        mock_message.reply_text = AsyncMock()
        
        # Mock 已运行的监控服务
        with patch('module.disk.commands.disk_monitor.get_global_monitor_service') as mock_global_service:
            mock_running_service = MagicMock()
            mock_running_service.running = True
            mock_global_service.return_value = mock_running_service
            
            # 设置用户语言为 en_US
            with patch('module.i18n.services.i18n_manager.get_user_language') as mock_get_lang:
                mock_get_lang.return_value = 'en_US'
                
                # 执行命令
                await start_disk_monitor(mock_client, mock_message)
                
                # 获取发送的消息内容
                mock_message.reply_text.assert_called_once()
                sent_message = mock_message.reply_text.call_args[0][0]
                
                # 验证：不应该包含硬编码中文
                chinese_terms = [
                    "磁盘监控服务状态", "服务状态", "运行中", "操作结果", "已在运行"
                ]
                
                for term in chinese_terms:
                    self.assertNotIn(term, sent_message,
                                   f"已运行消息不应包含硬编码中文 '{term}'")
                
                # 验证：应该包含英文翻译
                self.assertTrue(
                    "already" in sent_message.lower() and "running" in sent_message.lower(),
                    "已运行消息应该包含英文翻译 'already running'"
                )
    
    async def test_i18n_manager_should_be_used_in_disk_commands(self):
        """
        失败测试：磁盘命令应该使用 i18n 管理器进行翻译
        """
        # 这个测试检查代码结构，验证是否导入和使用了 i18n
        
        # 检查 disk_monitor.py 是否导入了 i18n 相关模块
        import inspect
        import module.disk.commands.disk_monitor as disk_monitor_module
        
        source_code = inspect.getsource(disk_monitor_module)
        
        # 验证：应该导入 i18n 相关模块
        i18n_imports = [
            "from module.i18n import get_i18n_manager",
            "from module.i18n.services.i18n_manager import",
            "import module.i18n"
        ]
        
        has_i18n_import = any(imp in source_code for imp in i18n_imports)
        
        # 这个测试会失败，因为当前没有导入 i18n
        self.assertTrue(has_i18n_import, 
                       "disk_monitor.py 应该导入并使用 i18n 翻译系统")
        
        # 验证：应该有调用翻译方法的代码
        translation_calls = [
            ".translate_for_user(",
            ".translate(",
            "i18n.translate",
            "translate_for_user"
        ]
        
        has_translation_calls = any(call in source_code for call in translation_calls)
        
        # 这个测试会失败，因为当前没有使用翻译方法
        self.assertTrue(has_translation_calls,
                       "disk_monitor.py 应该调用翻译方法而不是硬编码消息")


if __name__ == '__main__':
    print("=" * 70)
    print("TDD 红灯阶段 - 磁盘命令国际化修复测试")
    print("=" * 70)
    print("问题分析：")
    print("1. /disk 命令消息硬编码中文，不支持多语言")
    print("2. 用户切换为 en_US 后仍显示中文消息")
    print("3. 缺少 i18n 翻译系统的集成和使用")
    print("=" * 70)
    
    async def run_failing_tests():
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestDiskCommandI18nFix)
        
        passed = 0
        failed = 0
        
        for test in suite:
            test_method = getattr(test, test._testMethodName)
            if asyncio.iscoroutinefunction(test_method):
                try:
                    await test_method(test)
                    print(f"🟢 {test._testMethodName} - 意外通过（应该失败）")
                    passed += 1
                except AssertionError as e:
                    print(f"🔴 {test._testMethodName} - 按预期失败: {str(e)[:80]}...")
                    failed += 1
                except Exception as e:
                    print(f"❌ {test._testMethodName} - 错误: {str(e)[:80]}...")
                    failed += 1
            else:
                try:
                    test_method(test)
                    print(f"🟢 {test._testMethodName} - 意外通过（应该失败）")
                    passed += 1
                except AssertionError as e:
                    print(f"🔴 {test._testMethodName} - 按预期失败: {str(e)[:80]}...")
                    failed += 1
                except Exception as e:
                    print(f"❌ {test._testMethodName} - 错误: {str(e)[:80]}...")
                    failed += 1
        
        print("=" * 70)
        print(f"红灯阶段结果：通过 {passed}，失败 {failed}")
        if failed > 0:
            print("✅ 测试按预期失败，确认了国际化问题的存在")
        print("=" * 70)
    
    asyncio.run(run_failing_tests())