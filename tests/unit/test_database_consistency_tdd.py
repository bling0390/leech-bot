"""
TDD 红灯阶段：数据库操作一致性测试

验证所有数据库操作使用一致的数据库名称和配置
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestDatabaseConsistency(unittest.TestCase):
    """数据库操作一致性测试"""
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_all_database_operations_use_same_database_name(self, mock_get_client):
        """
        失败测试：所有数据库操作应该使用相同的数据库名称
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
        
        # Mock UserLanguage.get_user_language 返回 None（强制使用异步方法）
        with patch('beans.user_language.UserLanguage.get_user_language', return_value=None):
            # 执行所有数据库相关操作
            await get_user_language(123)
            await save_user_language_async(456, 'zh_CN')
            await get_motor_collection('test_collection')
            
            # 收集所有数据库访问调用
            db_calls = [call[0][0] for call in mock_client.__getitem__.call_args_list]
            
            # 验证：所有调用应该使用相同的数据库名称
            unique_db_names = set(db_calls)
            self.assertEqual(len(unique_db_names), 1, 
                           f"所有操作应该使用相同的数据库名称，实际使用了: {unique_db_names}")
            
            # 验证：使用的应该是 'bot' 数据库
            expected_db_name = 'bot'
            self.assertEqual(list(unique_db_names)[0], expected_db_name,
                           f"应该使用 '{expected_db_name}' 数据库，实际使用了: {list(unique_db_names)[0]}")
    
    async def test_database_configuration_centralization(self):
        """
        失败测试：数据库配置应该集中管理
        """
        import module.i18n.services.i18n_manager as i18n_module
        
        # 检查是否有集中的数据库配置
        config_attributes = [
            'DATABASE_NAME',
            'DB_CONFIG', 
            'MONGO_DATABASE',
            'DEFAULT_DATABASE'
        ]
        
        has_config = any(hasattr(i18n_module, attr) for attr in config_attributes)
        
        # 这个测试会失败，因为当前没有集中的数据库配置
        self.assertTrue(has_config, 
                       "应该有集中的数据库配置常量，如 DATABASE_NAME 等")
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_database_name_parameter_consistency(self, mock_get_client):
        """
        失败测试：验证所有函数使用一致的数据库名称参数
        """
        # Mock Motor client
        mock_client = AsyncMock()
        mock_db = AsyncMock()
        mock_collection = AsyncMock()
        
        mock_get_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # Mock 返回值
        mock_collection.find_one.return_value = None
        mock_result = MagicMock()
        mock_result.modified_count = 0
        mock_result.upserted_id = "new_id"
        mock_collection.update_one.return_value = mock_result
        
        from module.i18n.services.i18n_manager import save_user_language_async
        
        # 执行操作
        await save_user_language_async(789, 'en_US')
        
        # 验证数据库访问
        mock_client.__getitem__.assert_called()
        db_call = mock_client.__getitem__.call_args[0][0]
        
        # 这个测试会失败，因为当前使用 'alist_bot'
        self.assertEqual(db_call, 'bot', 
                        f"数据库名称应该是 'bot'，实际是 '{db_call}'")
    
    async def test_no_mixed_database_names_in_single_operation(self):
        """
        失败测试：单个操作中不应该混合使用不同的数据库名称
        """
        with patch('tool.mongo_client.get_motor_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_db1 = AsyncMock()
            mock_db2 = AsyncMock()
            mock_collection = AsyncMock()
            
            # 设置不同数据库的 mock
            def mock_getitem(db_name):
                if db_name == 'bot':
                    return mock_db1
                elif db_name == 'alist_bot':
                    return mock_db2
                else:
                    return AsyncMock()
            
            mock_client.__getitem__.side_effect = mock_getitem
            mock_get_client.return_value = mock_client
            
            mock_db1.__getitem__.return_value = mock_collection
            mock_db2.__getitem__.return_value = mock_collection
            
            # Mock 返回值
            mock_collection.find_one.return_value = None
            
            from module.i18n.services.i18n_manager import get_user_language
            
            # Mock UserLanguage.get_user_language 返回 None
            with patch('beans.user_language.UserLanguage.get_user_language', return_value=None):
                await get_user_language(123)
                
                # 收集数据库调用
                db_calls = [call[0][0] for call in mock_client.__getitem__.call_args_list]
                
                # 验证：不应该同时访问 'bot' 和 'alist_bot'
                has_bot = 'bot' in db_calls
                has_alist_bot = 'alist_bot' in db_calls
                
                # 这个测试可能失败，如果代码中混合使用了数据库名称
                self.assertFalse(has_bot and has_alist_bot, 
                               "不应该在同一操作中混合使用 'bot' 和 'alist_bot' 数据库")
                
                # 优先应该使用 'bot'
                if db_calls:
                    self.assertEqual(db_calls[0], 'bot', 
                                   f"应该优先使用 'bot' 数据库，实际使用了 '{db_calls[0]}'")
    
    async def test_database_name_environment_configuration(self):
        """
        失败测试：数据库名称应该可以通过环境变量配置
        """
        import os
        import module.i18n.services.i18n_manager as i18n_module
        
        # 检查是否支持环境变量配置
        # 这个测试会失败，因为当前代码没有环境变量支持
        
        # 模拟设置环境变量
        original_env = os.environ.get('MONGO_DATABASE')
        os.environ['MONGO_DATABASE'] = 'test_bot'
        
        try:
            # 检查模块是否读取环境变量
            has_env_support = (
                hasattr(i18n_module, 'get_database_name') or
                'MONGO_DATABASE' in str(i18n_module.__dict__) or
                'os.environ' in str(i18n_module.__dict__)
            )
            
            self.assertTrue(has_env_support, 
                           "应该支持通过环境变量配置数据库名称")
            
        finally:
            # 恢复环境变量
            if original_env is not None:
                os.environ['MONGO_DATABASE'] = original_env
            elif 'MONGO_DATABASE' in os.environ:
                del os.environ['MONGO_DATABASE']
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_database_connection_reuse(self, mock_get_client):
        """
        失败测试：应该复用数据库连接而不是重复创建
        """
        from module.i18n.services.i18n_manager import save_user_language_async
        
        # Mock Motor client
        mock_client = AsyncMock()
        mock_db = AsyncMock()
        mock_collection = AsyncMock()
        
        mock_get_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # Mock successful operations
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_result.upserted_id = None
        mock_collection.update_one.return_value = mock_result
        
        # 执行多次操作
        await save_user_language_async(123, 'en_US')
        await save_user_language_async(456, 'zh_CN')
        
        # 验证：get_motor_client 应该被调用，但数据库访问应该一致
        self.assertTrue(mock_get_client.called, "应该调用 get_motor_client")
        
        # 收集所有数据库访问
        db_calls = [call[0][0] for call in mock_client.__getitem__.call_args_list]
        
        # 验证：所有调用都使用相同的数据库名称
        self.assertTrue(all(db == 'bot' for db in db_calls),
                       f"所有数据库访问都应该使用 'bot'，实际使用: {set(db_calls)}")


if __name__ == '__main__':
    print("=" * 70)
    print("TDD 红灯阶段 - 数据库操作一致性测试")
    print("=" * 70)
    print("这些测试验证数据库操作的一致性：")
    print("1. 所有操作使用相同的数据库名称")
    print("2. 集中的数据库配置管理")
    print("3. 环境变量支持和连接复用")
    print("=" * 70)
    
    async def run_consistency_tests():
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestDatabaseConsistency)
        
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
        
        print("=" * 70)
        print(f"一致性测试结果：通过 {passed}，失败 {failed}")
        print("=" * 70)
    
    asyncio.run(run_consistency_tests())