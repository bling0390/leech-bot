"""
TDD 红灯阶段：测试用户语言偏好数据库写入问题

这个测试文件专门测试用户语言偏好应该正确写入 user_language 表，
而不是写入错误的集合或者根本没有写入。

问题描述：
1. UserLanguage 模型使用 'user_language' 集合
2. 但 i18n_manager 中的异步保存函数使用 'lang' 集合
3. 导致数据不一致和语言偏好无法正确保存
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from datetime import datetime


class TestUserLanguageDatabaseFix(unittest.TestCase):
    """TDD 红灯阶段：测试用户语言数据库写入修复"""
    
    @patch('beans.user_language.UserLanguage.objects')
    async def test_user_language_should_write_to_user_language_collection(self, mock_objects):
        """
        失败测试：用户语言偏好应该写入 user_language 集合
        
        这个测试会失败，因为当前代码存在集合名称不一致的问题
        """
        from beans.user_language import UserLanguage
        
        # Mock QuerySet 行为
        mock_queryset = MagicMock()
        mock_objects.return_value = mock_queryset
        mock_queryset.first.return_value = None  # 模拟用户不存在
        
        # Mock 保存操作
        mock_user_lang = MagicMock()
        mock_user_lang.save = MagicMock()
        
        with patch.object(UserLanguage, '__init__', return_value=None) as mock_init:
            mock_init.return_value = None
            with patch.object(UserLanguage, 'save') as mock_save:
                # 测试设置用户语言
                result = UserLanguage.set_user_language(123456, 'en_US')
                
                # 验证：应该创建新记录并保存到正确的集合
                # 这个断言会失败，因为当前实现存在问题
                self.assertTrue(result)
                
                # 关键验证：检查集合名称
                meta_collection = UserLanguage._meta['collection']
                self.assertEqual(meta_collection, 'user_language', 
                    "UserLanguage 模型必须使用 'user_language' 集合名称")
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_async_save_should_use_correct_collection_name(self, mock_get_client):
        """
        失败测试：异步保存应该使用正确的集合名称
        
        当前 save_user_language_async 使用 'lang' 集合，应该使用 'user_language'
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
        result = await save_user_language_async(123456, 'en_US')
        
        # 验证：应该使用 'user_language' 集合名称
        # 这个测试会失败，因为当前代码使用 'lang' 集合
        mock_db.__getitem__.assert_called_with('user_language')
        self.assertNotEqual(mock_db.__getitem__.call_args[0][0], 'lang',
            "异步保存不应该使用 'lang' 集合，应该使用 'user_language'")
        
        self.assertTrue(result)
    
    @patch('tool.mongo_client.get_motor_client')
    @patch('beans.user_language.UserLanguage.objects')
    async def test_data_consistency_between_sync_and_async_operations(self, mock_objects, mock_get_client):
        """
        失败测试：同步和异步操作应该使用相同的数据库集合
        
        验证 UserLanguage.set_user_language 和 save_user_language_async 
        应该操作同一个集合，确保数据一致性
        """
        from beans.user_language import UserLanguage
        from module.i18n.services.i18n_manager import save_user_language_async
        
        # 测试同步操作使用的集合名称
        sync_collection = UserLanguage._meta['collection']
        
        # Mock Motor client for async operation
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
        
        # 执行异步操作
        await save_user_language_async(123456, 'en_US')
        
        # 获取异步操作使用的集合名称
        async_collection_call = mock_db.__getitem__.call_args[0][0]
        
        # 验证：两个操作应该使用相同的集合名称
        # 这个测试会失败，因为当前同步用 'user_language'，异步用 'lang'
        self.assertEqual(sync_collection, async_collection_call,
            f"同步操作使用 '{sync_collection}' 集合，异步操作使用 '{async_collection_call}' 集合。"
            f"两者必须一致！")
    
    async def test_user_language_model_fields_validation(self):
        """
        失败测试：验证 UserLanguage 模型字段定义
        
        确保模型字段与数据库操作中使用的字段名称一致
        """
        from beans.user_language import UserLanguage
        
        # 获取模型字段
        model_fields = []
        for field_name, field in UserLanguage._fields.items():
            model_fields.append(field_name)
        
        # 验证必需字段存在
        required_fields = ['user_id', 'language_code', 'created_at', 'updated_at']
        for field in required_fields:
            self.assertIn(field, model_fields,
                f"UserLanguage 模型缺少必需字段: {field}")
        
        # 验证字段类型
        user_id_field = UserLanguage._fields['user_id']
        self.assertEqual(user_id_field.__class__.__name__, 'IntField',
            "user_id 字段应该是 IntField 类型")
        
        # 验证唯一性约束
        self.assertTrue(user_id_field.unique,
            "user_id 字段应该有唯一性约束")
    
    @patch('module.i18n.services.i18n_manager.get_motor_client')
    async def test_language_preference_persistence_after_restart(self, mock_get_client):
        """
        失败测试：验证语言偏好在系统重启后仍然存在
        
        模拟保存语言偏好后系统重启，检查数据是否正确持久化
        """
        from module.i18n.services.i18n_manager import save_user_language_async, get_user_language
        
        # Mock Motor client
        mock_client = AsyncMock()
        mock_db = AsyncMock()
        mock_collection = AsyncMock()
        
        mock_get_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # Mock 保存操作成功
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_result.upserted_id = None
        mock_collection.update_one.return_value = mock_result
        
        # Mock 查询操作
        mock_collection.find_one.return_value = {
            'user_id': 123456,
            'language_code': 'en_US',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # 测试保存
        save_result = await save_user_language_async(123456, 'en_US')
        self.assertTrue(save_result)
        
        # 测试查询（模拟重启后查询）
        retrieved_language = await get_user_language(123456)
        
        # 验证：应该返回之前保存的语言
        # 这可能会失败，因为数据存储和查询可能使用不同的集合
        self.assertEqual(retrieved_language, 'en_US',
            "系统重启后应该能正确获取用户语言偏好")
    
    @patch('beans.user_language.UserLanguage.objects')
    async def test_upsert_operation_for_existing_user(self, mock_objects):
        """
        失败测试：验证现有用户的语言偏好更新操作
        
        测试当用户已存在语言记录时，应该更新而不是创建新记录
        """
        from beans.user_language import UserLanguage
        
        # Mock 现有用户记录
        mock_existing_user = MagicMock()
        mock_existing_user.language_code = 'zh_CN'
        mock_existing_user.save = MagicMock()
        
        mock_queryset = MagicMock()
        mock_objects.return_value = mock_queryset
        mock_queryset.first.return_value = mock_existing_user
        
        # 执行语言更新
        result = UserLanguage.set_user_language(123456, 'en_US')
        
        # 验证：应该更新现有记录
        self.assertTrue(result)
        mock_existing_user.save.assert_called_once()
        
        # 验证：语言代码应该被更新
        self.assertEqual(mock_existing_user.language_code, 'en_US',
            "现有用户的语言代码应该被正确更新")
    
    async def test_error_handling_for_database_failures(self):
        """
        失败测试：验证数据库操作失败时的错误处理
        
        测试当数据库连接失败或操作异常时，函数应该优雅地处理错误
        """
        from module.i18n.services.i18n_manager import save_user_language_async
        
        with patch('tool.mongo_client.get_motor_client') as mock_get_client:
            # Mock 数据库连接失败
            mock_get_client.side_effect = Exception("Database connection failed")
            
            # 执行保存操作
            result = await save_user_language_async(123456, 'en_US')
            
            # 验证：应该返回 False 而不是抛出异常
            self.assertFalse(result,
                "数据库操作失败时应该返回 False，而不是抛出异常")


if __name__ == '__main__':
    print("=" * 60)
    print("TDD 红灯阶段 - 用户语言数据库写入问题测试")
    print("=" * 60)
    print("这些测试预期会失败，暴露当前实现中的问题：")
    print("1. 集合名称不一致（user_language vs lang）")
    print("2. 同步和异步操作不一致")
    print("3. 数据持久化问题")
    print("=" * 60)
    
    async def run_failing_tests():
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestUserLanguageDatabaseFix)
        
        for test in suite:
            test_method = getattr(test, test._testMethodName)
            if asyncio.iscoroutinefunction(test_method):
                try:
                    await test_method(test)
                    print(f"🟢 {test._testMethodName} - 意外通过（应该失败）")
                except AssertionError as e:
                    print(f"🔴 {test._testMethodName} - 按预期失败: {str(e)[:100]}...")
                except Exception as e:
                    print(f"❌ {test._testMethodName} - 错误: {str(e)[:100]}...")
    
    asyncio.run(run_failing_tests())