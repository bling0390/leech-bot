"""
TDD 绿灯阶段：验证用户语言数据库写入修复

这个测试文件验证修复后的代码是否能正确工作
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestUserLanguageFixVerification(unittest.TestCase):
    """TDD 绿灯阶段：验证用户语言修复"""
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_async_save_now_uses_correct_collection(self, mock_get_client):
        """
        绿灯测试：异步保存现在使用正确的集合名称
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
        
        # 验证：现在应该使用 'user_language' 集合名称
        mock_db.__getitem__.assert_called_with('user_language')
        self.assertTrue(result)
        
        # 验证：更新操作包含正确的字段
        update_call = mock_collection.update_one.call_args
        update_data = update_call[0][1]['$set']
        
        self.assertIn('user_id', update_data)
        self.assertIn('language_code', update_data)
        self.assertIn('updated_at', update_data)
        self.assertEqual(update_data['language_code'], 'en_US')
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_async_get_now_uses_correct_collection(self, mock_get_client):
        """
        绿灯测试：异步获取现在使用正确的集合名称
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
        
        # Mock UserLanguage.get_user_language 返回 None（模拟同步方法失败）
        with patch('beans.user_language.UserLanguage.get_user_language', return_value=None):
            # 执行异步获取
            result = await get_user_language(123456)
            
            # 验证：现在应该使用 'user_language' 集合名称
            mock_db.__getitem__.assert_called_with('user_language')
            self.assertEqual(result, 'en_US')
    
    @patch('beans.user_language.UserLanguage.objects')
    def test_sync_save_error_handling_improved(self, mock_objects):
        """
        绿灯测试：同步保存的错误处理已改进
        """
        from beans.user_language import UserLanguage
        
        # Mock 数据库操作失败
        mock_objects.side_effect = Exception("Database error")
        
        # 执行保存操作
        result = UserLanguage.set_user_language(123456, 'en_US')
        
        # 验证：应该返回 False 而不是抛出异常
        self.assertFalse(result)
    
    async def test_data_consistency_between_operations(self):
        """
        绿灯测试：同步和异步操作现在使用相同的集合
        """
        from beans.user_language import UserLanguage
        
        # 获取同步操作使用的集合名称
        sync_collection = UserLanguage._meta['collection']
        
        # 验证：应该是 'user_language'
        self.assertEqual(sync_collection, 'user_language')
        
        # 这确保了同步和异步操作现在使用相同的集合名称
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    async def test_language_switch_flow_now_works(self, mock_get_i18n):
        """
        绿灯测试：完整的语言切换流程现在能正常工作
        """
        from module.i18n.commands.lang_command import handle_lang_callback
        
        # Mock i18n manager
        mock_i18n = MagicMock()
        mock_get_i18n.return_value = mock_i18n
        
        # Mock 语言验证通过
        mock_i18n.get_available_languages.return_value = [
            {'code': 'zh_CN', 'name': 'Chinese (Simplified)', 'native_name': '简体中文'},
            {'code': 'en_US', 'name': 'English', 'native_name': 'English'}
        ]
        
        # Mock 保存成功（现在应该工作）
        mock_i18n.save_user_language = AsyncMock(return_value=True)
        mock_i18n.translate_for_user = AsyncMock(return_value="✅ Language changed to: English")
        
        # 创建回调查询
        from pyrogram.types import CallbackQuery
        mock_client = AsyncMock()
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.data = "lang_en_US"
        mock_callback.from_user.id = 123456
        mock_callback.message.delete = AsyncMock()
        mock_callback.answer = AsyncMock()
        
        # 执行完整流程
        await handle_lang_callback(mock_client, mock_callback)
        
        # 验证：保存方法应该被调用
        mock_i18n.save_user_language.assert_called_once_with(123456, 'en_US')
        
        # 验证：用户应该收到成功消息
        mock_callback.answer.assert_called_once()
        success_message = mock_callback.answer.call_args[0][0]
        self.assertIn("✅", success_message)
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_upsert_creates_record_with_timestamps(self, mock_get_client):
        """
        绿灯测试：upsert操作现在创建包含时间戳的记录
        """
        from module.i18n.services.i18n_manager import save_user_language_async
        
        # Mock Motor client
        mock_client = AsyncMock()
        mock_db = AsyncMock()
        mock_collection = AsyncMock()
        
        mock_get_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # Mock successful insert (new record)
        mock_result = MagicMock()
        mock_result.modified_count = 0
        mock_result.upserted_id = "new_record_id"
        mock_collection.update_one.return_value = mock_result
        
        # 执行保存操作
        result = await save_user_language_async(123456, 'zh_CN')
        
        # 验证：操作成功
        self.assertTrue(result)
        
        # 验证：更新操作包含时间戳字段
        update_call = mock_collection.update_one.call_args
        set_data = update_call[0][1]['$set']
        set_on_insert = update_call[0][1]['$setOnInsert']
        
        # 验证更新字段
        self.assertIn('updated_at', set_data)
        # 验证插入时设置的字段
        self.assertIn('created_at', set_on_insert)


if __name__ == '__main__':
    print("=" * 60)
    print("TDD 绿灯阶段 - 验证用户语言数据库修复")
    print("=" * 60)
    print("验证修复后的代码：")
    print("1. 异步操作使用正确的集合名称")
    print("2. 数据模型字段一致性")
    print("3. 完整流程现在能正常工作")
    print("=" * 60)
    
    async def run_verification_tests():
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestUserLanguageFixVerification)
        
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
            else:
                try:
                    test_method(test)
                    print(f"🟢 {test._testMethodName} - 通过")
                    passed += 1
                except AssertionError as e:
                    print(f"🔴 {test._testMethodName} - 失败: {str(e)[:100]}...")
                    failed += 1
                except Exception as e:
                    print(f"❌ {test._testMethodName} - 错误: {str(e)[:100]}...")
                    failed += 1
        
        print("=" * 60)
        print(f"测试结果：通过 {passed}，失败 {failed}")
        if failed == 0:
            print("🎉 所有测试通过！语言数据库写入问题已修复！")
        else:
            print("⚠️ 仍有测试失败，需要进一步修复")
        print("=" * 60)
    
    asyncio.run(run_verification_tests())