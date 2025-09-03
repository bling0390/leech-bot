"""
TDD 红灯阶段：数据库名称修正测试

测试确保所有数据库操作使用正确的数据库名称 'bot' 而不是 'alist_bot'
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestDatabaseNameFix(unittest.TestCase):
    """TDD 红灯阶段：数据库名称修正测试"""
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_async_get_user_language_should_use_bot_database(self, mock_get_client):
        """
        失败测试：异步获取用户语言应该使用 'bot' 数据库
        
        当前代码使用 'alist_bot'，需要修正为 'bot'
        """
        from module.i18n.services.i18n_manager import get_user_language
        
        # Mock Motor client
        mock_client = AsyncMock()
        mock_db = AsyncMock()
        mock_collection = AsyncMock()
        
        mock_get_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # Mock 查询结果
        mock_collection.find_one.return_value = {
            'user_id': 123456,
            'language_code': 'en_US'
        }
        
        # Mock UserLanguage.get_user_language 返回 None（强制使用异步方法）
        with patch('beans.user_language.UserLanguage.get_user_language', return_value=None):
            # 执行异步获取
            await get_user_language(123456)
            
            # 验证：应该使用 'bot' 数据库而不是 'alist_bot'
            # 这个测试会失败，因为当前代码使用 'alist_bot'
            mock_client.__getitem__.assert_called_with('bot')
            
            # 确保没有使用错误的数据库名称
            calls = [call[0][0] for call in mock_client.__getitem__.call_args_list]
            self.assertNotIn('alist_bot', calls, "不应该使用 'alist_bot' 数据库名称")
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_async_save_user_language_should_use_bot_database(self, mock_get_client):
        """
        失败测试：异步保存用户语言应该使用 'bot' 数据库
        """
        from module.i18n.services.i18n_manager import save_user_language_async
        
        # Mock Motor client
        mock_client = AsyncMock()
        mock_db = AsyncMock()
        mock_collection = AsyncMock()
        
        mock_get_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # Mock successful update
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_result.upserted_id = None
        mock_collection.update_one.return_value = mock_result
        
        # 执行异步保存
        await save_user_language_async(123456, 'en_US')
        
        # 验证：应该使用 'bot' 数据库
        # 这个测试会失败，因为当前代码使用 'alist_bot'
        mock_client.__getitem__.assert_called_with('bot')
        
        # 确保没有使用错误的数据库名称
        calls = [call[0][0] for call in mock_client.__getitem__.call_args_list]
        self.assertNotIn('alist_bot', calls, "不应该使用 'alist_bot' 数据库名称")
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_get_motor_collection_should_use_bot_database(self, mock_get_client):
        """
        失败测试：get_motor_collection 函数应该使用 'bot' 数据库
        """
        from module.i18n.services.i18n_manager import get_motor_collection
        
        # Mock Motor client
        mock_client = AsyncMock()
        mock_db = AsyncMock()
        mock_collection = AsyncMock()
        
        mock_get_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # 执行获取集合操作
        await get_motor_collection('test_collection')
        
        # 验证：应该使用 'bot' 数据库
        # 这个测试会失败，因为当前代码使用 'alist_bot'
        mock_client.__getitem__.assert_called_with('bot')
        
        # 确保没有使用错误的数据库名称
        calls = [call[0][0] for call in mock_client.__getitem__.call_args_list]
        self.assertNotIn('alist_bot', calls, "不应该使用 'alist_bot' 数据库名称")
    
    async def test_database_name_consistency_across_functions(self):
        """
        失败测试：所有数据库操作应该使用一致的数据库名称
        """
        with patch('tool.mongo_client.get_motor_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_db = AsyncMock()
            mock_collection = AsyncMock()
            
            mock_get_client.return_value = mock_client
            mock_client.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection
            
            # Mock 各种返回值
            mock_collection.find_one.return_value = {'user_id': 123, 'language_code': 'en_US'}
            mock_result = MagicMock()
            mock_result.modified_count = 1
            mock_result.upserted_id = None
            mock_collection.update_one.return_value = mock_result
            
            from module.i18n.services.i18n_manager import get_user_language, save_user_language_async, get_motor_collection
            
            # Mock UserLanguage.get_user_language 返回 None
            with patch('beans.user_language.UserLanguage.get_user_language', return_value=None):
                # 执行多个数据库操作
                await get_user_language(123)
                await save_user_language_async(123, 'en_US')
                await get_motor_collection('test')
                
                # 获取所有数据库调用
                db_calls = [call[0][0] for call in mock_client.__getitem__.call_args_list]
                
                # 验证：所有调用都应该使用 'bot' 数据库
                expected_calls = ['bot', 'bot', 'bot']
                self.assertEqual(db_calls, expected_calls, "所有数据库操作应该使用 'bot' 数据库")
                
                # 验证：不应该有任何 'alist_bot' 调用
                self.assertNotIn('alist_bot', db_calls, "不应该使用 'alist_bot' 数据库名称")
    
    async def test_database_name_constant_definition(self):
        """
        失败测试：验证是否应该定义数据库名称常量
        
        建议在模块中定义 DATABASE_NAME 常量以避免硬编码
        """
        # 检查模块中是否定义了数据库名称常量
        import module.i18n.services.i18n_manager as i18n_module
        
        # 这个测试会失败，因为当前没有定义常量
        self.assertTrue(hasattr(i18n_module, 'DATABASE_NAME'), 
                       "应该定义 DATABASE_NAME 常量以避免硬编码数据库名称")
        
        if hasattr(i18n_module, 'DATABASE_NAME'):
            self.assertEqual(i18n_module.DATABASE_NAME, 'bot',
                           "DATABASE_NAME 常量应该设置为 'bot'")
    
    async def test_no_hardcoded_alist_bot_strings(self):
        """
        失败测试：验证代码中不应该存在硬编码的 'alist_bot' 字符串
        """
        import module.i18n.services.i18n_manager as i18n_module
        import inspect
        
        # 获取模块源代码
        source_code = inspect.getsource(i18n_module)
        
        # 检查是否存在硬编码的 'alist_bot'
        # 这个测试会失败，因为当前代码中存在 'alist_bot'
        self.assertNotIn("'alist_bot'", source_code, 
                        "代码中不应该存在硬编码的 'alist_bot' 字符串")
        self.assertNotIn('"alist_bot"', source_code, 
                        "代码中不应该存在硬编码的 'alist_bot' 字符串")
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_error_handling_with_correct_database_name(self, mock_get_client):
        """
        失败测试：错误处理中也应该使用正确的数据库名称
        """
        from module.i18n.services.i18n_manager import save_user_language_async
        
        # Mock Motor client 抛出异常
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_client.__getitem__.side_effect = Exception("Database connection failed")
        
        # 执行操作（应该失败但优雅处理）
        result = await save_user_language_async(123456, 'en_US')
        
        # 验证：即使在错误情况下，也应该尝试访问 'bot' 数据库
        # 这个测试会失败，因为当前代码使用 'alist_bot'
        mock_client.__getitem__.assert_called_with('bot')
        
        # 验证：操作失败返回 False
        self.assertFalse(result)


if __name__ == '__main__':
    print("=" * 70)
    print("TDD 红灯阶段 - 数据库名称修正测试")
    print("=" * 70)
    print("这些测试预期会失败，暴露当前实现中的问题：")
    print("1. 使用 'alist_bot' 而不是 'bot' 作为数据库名称")
    print("2. 缺乏数据库名称常量定义")
    print("3. 硬编码数据库名称带来的一致性问题")
    print("=" * 70)
    
    async def run_failing_tests():
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestDatabaseNameFix)
        
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
        
        print("=" * 70)
        print(f"红灯阶段结果：通过 {passed}，失败 {failed}")
        if failed > 0:
            print("✅ 测试按预期失败，现在可以开始实现修复代码")
        else:
            print("⚠️ 测试意外通过，可能需要调整测试用例")
        print("=" * 70)
    
    asyncio.run(run_failing_tests())