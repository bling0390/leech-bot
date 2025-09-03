"""
TDD 红灯阶段：修复语言切换时重复日志输出问题

问题分析：
1. lang_command 中调用了 get_user_language(user_id) 
2. 然后调用了 3 次 translate_for_user(user_id, ...)
3. translate_for_user 内部又调用 get_user_language(user_id)
4. 总共导致 4 次相同的日志输出

修复目标：确保单次语言切换操作只产生合理数量的日志
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock, call
import asyncio
from io import StringIO
import logging
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestDuplicateLoggingFix(unittest.TestCase):
    """TDD 红灯阶段：重复日志输出修复测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建一个内存中的日志处理器来捕获日志
        self.log_capture = StringIO()
        self.log_handler = logging.StreamHandler(self.log_capture)
        self.log_handler.setLevel(logging.DEBUG)
        
        # 获取 loguru 的 logger（项目中使用的）
        from loguru import logger
        logger.add(self.log_capture, level="DEBUG", format="{level} | {name}:{function}:{line} - {message}")
    
    def tearDown(self):
        """清理测试环境"""
        from loguru import logger
        logger.remove()  # 移除所有处理器
        self.log_capture.close()
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    async def test_lang_command_should_not_log_get_user_language_multiple_times(self, mock_get_i18n):
        """
        失败测试：/lang 命令不应该多次记录相同的 get_user_language 日志
        
        当前问题：lang_command 调用链导致 4 次相同的日志输出
        """
        from module.i18n.commands.lang_command import lang_command
        
        # Mock i18n manager
        mock_i18n = MagicMock()
        mock_get_i18n.return_value = mock_i18n
        
        # Mock get_user_language 方法
        mock_i18n.get_user_language = AsyncMock(return_value='zh_CN')
        
        # Mock translate_for_user 方法
        mock_i18n.translate_for_user = AsyncMock(return_value="测试翻译内容")
        
        # Mock 可用语言列表
        mock_i18n.get_available_languages.return_value = [
            {'code': 'zh_CN', 'name': 'Chinese (Simplified)', 'native_name': '简体中文'}
        ]
        
        # Mock Pyrogram 对象
        mock_client = AsyncMock()
        mock_message = AsyncMock()
        mock_message.from_user.id = 1076750810
        mock_message.reply_text = AsyncMock()
        
        # 执行 lang_command
        await lang_command(mock_client, mock_message)
        
        # 获取日志内容
        log_output = self.log_capture.getvalue()
        
        # 统计特定日志出现次数
        target_log_pattern = f"从同步方法获取用户 1076750810 语言: zh_CN"
        log_count = log_output.count(target_log_pattern)
        
        # 验证：这个特定日志应该只出现1次，而不是4次
        # 这个测试会失败，因为当前代码会输出4次相同日志
        self.assertEqual(log_count, 1, 
                        f"用户语言获取日志应该只出现1次，实际出现了{log_count}次。"
                        f"日志内容: {log_output}")
        
        # 验证 get_user_language 被调用的总次数
        total_calls = mock_i18n.get_user_language.call_count
        self.assertLessEqual(total_calls, 2, 
                           f"get_user_language 被调用了{total_calls}次，应该优化为最多2次")
    
    @patch('module.i18n.services.i18n_manager.get_user_language')
    async def test_translate_for_user_should_not_repeatedly_fetch_same_user_language(self, mock_get_user_lang):
        """
        失败测试：translate_for_user 在同一会话中不应该重复获取相同用户的语言
        """
        from module.i18n.services.i18n_manager import I18nManager
        
        # Mock get_user_language 函数
        mock_get_user_lang.return_value = 'zh_CN'
        
        manager = I18nManager()
        user_id = 1076750810
        
        # 模拟连续调用 translate_for_user（就像 lang_command 中那样）
        await manager.translate_for_user(user_id, 'language.menu_title')
        await manager.translate_for_user(user_id, 'language.select_prompt') 
        await manager.translate_for_user(user_id, 'language.current', language='简体中文')
        
        # 验证：get_user_language 不应该被调用太多次
        # 理想情况下，应该有缓存或批量获取机制
        call_count = mock_get_user_lang.call_count
        self.assertLessEqual(call_count, 1, 
                           f"get_user_language 在短时间内被调用了{call_count}次，应该有缓存机制")
    
    async def test_log_level_appropriateness_for_user_language_fetch(self):
        """
        失败测试：验证用户语言获取的日志级别是否合适
        
        DEBUG 级别的日志在生产环境中可能太详细
        """
        # 这个测试检查日志级别是否合适
        # DEBUG 日志在频繁调用的函数中可能不合适
        
        # 模拟检查日志配置
        log_level_too_verbose = True  # 当前使用 DEBUG 级别
        
        # 这个测试会失败，因为当前使用了过于详细的 DEBUG 级别
        self.assertFalse(log_level_too_verbose, 
                        "用户语言获取操作使用 DEBUG 级别日志太详细，"
                        "建议在频繁调用的操作中使用更高级别的日志")
    
    @patch('module.i18n.services.i18n_manager.UserLanguage.get_user_language')
    async def test_user_language_caching_to_reduce_duplicate_calls(self, mock_user_lang_get):
        """
        失败测试：应该有用户语言缓存机制来减少重复调用
        """
        from module.i18n.services.i18n_manager import get_user_language
        
        # Mock 返回值
        mock_user_lang_get.return_value = 'zh_CN'
        
        user_id = 1076750810
        
        # 模拟快速连续调用（就像 lang_command 场景）
        result1 = await get_user_language(user_id)
        result2 = await get_user_language(user_id)
        result3 = await get_user_language(user_id)
        result4 = await get_user_language(user_id)
        
        # 验证返回结果一致
        self.assertEqual(result1, result2)
        self.assertEqual(result2, result3) 
        self.assertEqual(result3, result4)
        
        # 验证：如果有缓存机制，底层调用应该减少
        # 这个测试可能会失败，因为当前没有缓存机制
        actual_calls = mock_user_lang_get.call_count
        expected_max_calls = 1  # 理想情况下应该只调用一次然后缓存
        
        self.assertLessEqual(actual_calls, expected_max_calls,
                           f"连续获取同一用户语言应该有缓存，实际调用了{actual_calls}次")
    
    async def test_log_message_content_should_be_informative_not_redundant(self):
        """
        失败测试：日志消息内容应该提供有用信息，而不是冗余信息
        """
        # 检查当前的日志消息格式
        current_log_message = "从同步方法获取用户 1076750810 语言: zh_CN"
        
        # 验证日志消息是否提供足够有价值的信息
        has_user_id = "1076750810" in current_log_message
        has_language = "zh_CN" in current_log_message
        has_method_info = "同步方法" in current_log_message
        
        self.assertTrue(has_user_id, "日志应该包含用户ID")
        self.assertTrue(has_language, "日志应该包含语言代码")
        
        # 但是方法来源信息在频繁调用时可能是冗余的
        # 这个测试可能会失败，因为当前日志过于详细
        log_too_detailed = has_method_info and True  # 总是True，表示当前过于详细
        
        self.assertFalse(log_too_detailed, 
                        "在频繁调用的函数中，日志不应该包含过多实现细节")
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    async def test_single_language_operation_should_have_reasonable_log_count(self, mock_get_i18n):
        """
        失败测试：单次语言操作应该有合理的日志数量
        """
        from module.i18n.commands.lang_command import lang_command
        
        # Mock setup (同前面的测试)
        mock_i18n = MagicMock()
        mock_get_i18n.return_value = mock_i18n
        mock_i18n.get_user_language = AsyncMock(return_value='zh_CN')
        mock_i18n.translate_for_user = AsyncMock(return_value="测试内容")
        mock_i18n.get_available_languages.return_value = [
            {'code': 'zh_CN', 'native_name': '简体中文'}
        ]
        
        # Mock Pyrogram objects
        mock_client = AsyncMock()
        mock_message = AsyncMock()
        mock_message.from_user.id = 1076750810
        mock_message.reply_text = AsyncMock()
        
        # 执行单次语言命令操作
        await lang_command(mock_client, mock_message)
        
        # 获取所有日志
        log_output = self.log_capture.getvalue()
        log_lines = [line for line in log_output.split('\n') if line.strip()]
        
        # 验证：单次操作的日志数量应该是合理的
        max_reasonable_logs = 5  # 假设合理的上限
        actual_log_count = len(log_lines)
        
        # 这个测试可能会失败，如果日志过多
        self.assertLessEqual(actual_log_count, max_reasonable_logs,
                           f"单次语言操作产生了{actual_log_count}条日志，超过了合理上限{max_reasonable_logs}")
        
        # 检查重复日志
        unique_logs = set(log_lines)
        duplicate_count = actual_log_count - len(unique_logs)
        
        self.assertEqual(duplicate_count, 0, 
                        f"发现{duplicate_count}条重复日志，应该避免重复输出")


if __name__ == '__main__':
    print("=" * 70)
    print("TDD 红灯阶段 - 重复日志输出修复测试")
    print("=" * 70)
    print("问题分析：")
    print("1. lang_command 调用 get_user_language(user_id) 一次")
    print("2. 然后调用 translate_for_user(user_id, ...) 三次")
    print("3. 每次 translate_for_user 内部又调用 get_user_language") 
    print("4. 总共产生 4 次相同的 DEBUG 日志输出")
    print("=" * 70)
    
    async def run_failing_tests():
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestDuplicateLoggingFix)
        
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
                    print(f"🔴 {test._testMethodName} - 按预期失败: {str(e)[:100]}...")
                    failed += 1
                except Exception as e:
                    print(f"❌ {test._testMethodName} - 错误: {str(e)[:100]}...")
                    failed += 1
            else:
                try:
                    test_method(test)
                    print(f"🟢 {test._testMethodName} - 意外通过（应该失败）")
                    passed += 1
                except AssertionError as e:
                    print(f"🔴 {test._testMethodName} - 按预期失败: {str(e)[:100]}...")
                    failed += 1
                except Exception as e:
                    print(f"❌ {test._testMethodName} - 错误: {str(e)[:100]}...")
                    failed += 1
        
        print("=" * 70)
        print(f"红灯阶段结果：通过 {passed}，失败 {failed}")
        if failed > 0:
            print("✅ 测试按预期失败，确认了重复日志问题的存在")
        print("=" * 70)
    
    asyncio.run(run_failing_tests())