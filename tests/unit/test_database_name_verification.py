"""
TDD 绿灯阶段：数据库名称修正验证测试

验证修复后的代码正确使用 'bot' 数据库名称
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestDatabaseNameVerification(unittest.TestCase):
    """TDD 绿灯阶段：数据库名称修正验证"""
    
    async def test_database_name_constant_exists(self):
        """
        绿灯测试：验证 DATABASE_NAME 常量已定义
        """
        import module.i18n.services.i18n_manager as i18n_module
        
        # 验证常量存在
        self.assertTrue(hasattr(i18n_module, 'DATABASE_NAME'), 
                       "DATABASE_NAME 常量应该已定义")
        
        # 验证常量值正确
        self.assertEqual(i18n_module.DATABASE_NAME, 'bot',
                        "DATABASE_NAME 应该设置为 'bot'")
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_get_user_language_now_uses_bot_database(self, mock_get_client):
        """
        绿灯测试：get_user_language 现在使用 'bot' 数据库
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
            result = await get_user_language(123456)
            
            # 验证：现在使用 'bot' 数据库
            mock_client.__getitem__.assert_called_with('bot')
            
            # 验证：返回正确结果
            self.assertEqual(result, 'en_US')
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_save_user_language_async_now_uses_bot_database(self, mock_get_client):
        """
        绿灯测试：save_user_language_async 现在使用 'bot' 数据库
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
        result = await save_user_language_async(123456, 'zh_CN')
        
        # 验证：使用 'bot' 数据库
        mock_client.__getitem__.assert_called_with('bot')
        
        # 验证：操作成功
        self.assertTrue(result)
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_get_motor_collection_now_uses_bot_database(self, mock_get_client):
        """
        绿灯测试：get_motor_collection 现在使用 'bot' 数据库
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
        result = await get_motor_collection('test_collection')
        
        # 验证：使用 'bot' 数据库
        mock_client.__getitem__.assert_called_with('bot')
        
        # 验证：返回集合对象
        self.assertEqual(result, mock_collection)
    
    async def test_no_hardcoded_alist_bot_strings_removed(self):
        """
        绿灯测试：验证硬编码的 'alist_bot' 字符串已移除
        """
        import module.i18n.services.i18n_manager as i18n_module
        import inspect
        
        # 获取模块源代码
        source_code = inspect.getsource(i18n_module)
        
        # 验证：不再存在硬编码的 'alist_bot'
        # 但仍可能存在在注释或常量定义中
        lines = source_code.split('\n')
        hardcoded_lines = [
            line for line in lines 
            if ("'alist_bot'" in line or '"alist_bot"' in line) 
            and not line.strip().startswith('#')  # 排除注释
            and 'DATABASE_NAME' not in line  # 排除常量定义相关
        ]
        
        self.assertEqual(len(hardcoded_lines), 0,
                        f"不应该存在硬编码的 'alist_bot' 字符串，发现: {hardcoded_lines}")
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_all_operations_use_consistent_database_name(self, mock_get_client):
        """
        绿灯测试：所有数据库操作使用一致的数据库名称
        """
        from module.i18n.services.i18n_manager import (
            get_user_language, save_user_language_async, get_motor_collection
        )
        
        # Mock Motor client
        mock_client = AsyncMock()
        mock_db = AsyncMock()
        mock_collection = AsyncMock()
        
        mock_get_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # Mock 返回值
        mock_collection.find_one.return_value = {'user_id': 123, 'language_code': 'en_US'}
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_result.upserted_id = None
        mock_collection.update_one.return_value = mock_result
        
        # Mock UserLanguage.get_user_language 返回 None
        with patch('beans.user_language.UserLanguage.get_user_language', return_value=None):
            # 执行所有数据库相关操作
            await get_user_language(123)
            await save_user_language_async(456, 'zh_CN')
            await get_motor_collection('test_collection')
            
            # 收集所有数据库访问调用
            db_calls = [call[0][0] for call in mock_client.__getitem__.call_args_list]
            
            # 验证：所有调用都使用 'bot' 数据库
            self.assertTrue(all(db == 'bot' for db in db_calls),
                           f"所有操作应该使用 'bot' 数据库，实际使用: {set(db_calls)}")
            
            # 验证：没有使用 'alist_bot'
            self.assertNotIn('alist_bot', db_calls,
                           "不应该再使用 'alist_bot' 数据库")
    
    async def test_database_name_constant_usage(self):
        """
        绿灯测试：验证代码使用了 DATABASE_NAME 常量而不是硬编码
        """
        import module.i18n.services.i18n_manager as i18n_module
        import inspect
        
        # 获取各个函数的源代码
        functions_to_check = [
            'get_user_language',
            'save_user_language_async', 
            'get_motor_collection'
        ]
        
        for func_name in functions_to_check:
            if hasattr(i18n_module, func_name):
                func = getattr(i18n_module, func_name)
                source = inspect.getsource(func)
                
                # 检查是否使用了 DATABASE_NAME 常量
                uses_constant = 'DATABASE_NAME' in source
                uses_hardcoded = ("client['bot']" in source or 'client["bot"]' in source)
                
                # 验证：应该使用常量而不是硬编码
                self.assertTrue(uses_constant or not uses_hardcoded,
                               f"函数 {func_name} 应该使用 DATABASE_NAME 常量")
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_error_handling_preserves_database_consistency(self, mock_get_client):
        """
        绿灯测试：错误处理时也保持数据库名称一致性
        """
        from module.i18n.services.i18n_manager import save_user_language_async
        
        # Mock Motor client 连接成功但操作失败
        mock_client = AsyncMock()
        mock_db = AsyncMock()
        mock_collection = AsyncMock()
        
        mock_get_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # Mock 操作失败
        mock_collection.update_one.side_effect = Exception("Update failed")
        
        # 执行操作（应该失败但优雅处理）
        result = await save_user_language_async(123456, 'en_US')
        
        # 验证：即使在错误情况下，也尝试访问了 'bot' 数据库
        mock_client.__getitem__.assert_called_with('bot')
        
        # 验证：操作返回 False
        self.assertFalse(result)


if __name__ == '__main__':
    print("=" * 70)
    print("TDD 绿灯阶段 - 数据库名称修正验证测试")
    print("=" * 70)
    print("验证修复后的代码：")
    print("1. 正确使用 'bot' 数据库名称")
    print("2. 定义了 DATABASE_NAME 常量")
    print("3. 移除了硬编码的 'alist_bot'")
    print("4. 所有操作保持一致性")
    print("=" * 70)
    
    async def run_verification_tests():
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestDatabaseNameVerification)
        
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
                    print(f"🔴 {test._testMethodName} - 失败: {str(e)[:100]}...")
                    failed += 1
                except Exception as e:
                    print(f"❌ {test._testMethodName} - 错误: {str(e)[:100]}...")
                    failed += 1
        
        print("=" * 70)
        print(f"绿灯阶段结果：通过 {passed}，失败 {failed}")
        if failed == 0:
            print("🎉 所有验证测试通过！数据库名称已成功修正！")
        else:
            print("⚠️ 部分测试失败，需要进一步修复")
        print("=" * 70)
    
    asyncio.run(run_verification_tests())