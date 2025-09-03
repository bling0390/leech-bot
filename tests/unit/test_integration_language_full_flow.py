"""
TDD 重构阶段：完整的语言选择流程集成测试

测试从用户交互到数据库持久化的完整端到端流程
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestLanguageFullFlowIntegration(unittest.TestCase):
    """完整语言选择流程集成测试"""
    
    @patch('tool.mongo_client.get_motor_client')
    @patch('beans.user_language.UserLanguage.objects')
    async def test_complete_language_switch_end_to_end(self, mock_objects, mock_get_client):
        """
        端到端测试：完整的语言切换流程
        
        测试流程：
        1. 用户点击语言按钮
        2. 验证语言代码
        3. 保存到数据库（同步和异步）
        4. 用户收到成功反馈
        5. 后续操作使用新语言
        """
        from module.i18n.commands.lang_command import handle_lang_callback
        from module.i18n.services.i18n_manager import get_user_language, save_user_language_async
        
        # Mock MongoDB操作
        mock_client = AsyncMock()
        mock_db = AsyncMock()
        mock_collection = AsyncMock()
        
        mock_get_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # Mock成功的数据库操作
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_result.upserted_id = None
        mock_collection.update_one.return_value = mock_result
        mock_collection.find_one.return_value = {
            'user_id': 123456,
            'language_code': 'en_US',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        
        # Mock UserLanguage同步操作
        mock_user_lang = MagicMock()
        mock_user_lang.language_code = 'en_US'
        mock_user_lang.save = MagicMock()
        
        mock_queryset = MagicMock()
        mock_objects.return_value = mock_queryset
        mock_queryset.first.return_value = None  # 模拟新用户
        
        # Mock i18n manager
        with patch('module.i18n.commands.lang_command.get_i18n_manager') as mock_get_i18n:
            mock_i18n = MagicMock()
            mock_get_i18n.return_value = mock_i18n
            
            # 设置可用语言
            mock_i18n.get_available_languages.return_value = [
                {'code': 'zh_CN', 'name': 'Chinese (Simplified)', 'native_name': '简体中文'},
                {'code': 'en_US', 'name': 'English', 'native_name': 'English'}
            ]
            
            # 设置异步保存方法
            async def mock_save_user_language(user_id, language):
                return await save_user_language_async(user_id, language)
            
            mock_i18n.save_user_language = mock_save_user_language
            mock_i18n.translate_for_user = AsyncMock(return_value="✅ Language changed to: English")
            
            # 创建回调查询
            from pyrogram.types import CallbackQuery
            mock_client_pyrogram = AsyncMock()
            mock_callback = AsyncMock(spec=CallbackQuery)
            mock_callback.data = "lang_en_US"
            mock_callback.from_user.id = 123456
            mock_callback.message.delete = AsyncMock()
            mock_callback.answer = AsyncMock()
            
            # 执行完整的语言切换流程
            await handle_lang_callback(mock_client_pyrogram, mock_callback)
            
            # 验证数据库写入操作
            mock_collection.update_one.assert_called_once()
            update_call = mock_collection.update_one.call_args
            
            # 验证写入的数据
            filter_dict = update_call[0][0]
            update_dict = update_call[0][1]
            
            self.assertEqual(filter_dict['user_id'], 123456)
            self.assertEqual(update_dict['$set']['language_code'], 'en_US')
            self.assertIn('updated_at', update_dict['$set'])
            self.assertIn('created_at', update_dict['$setOnInsert'])
            
            # 验证用户反馈
            mock_callback.answer.assert_called_once()
            success_message = mock_callback.answer.call_args[0][0]
            self.assertIn("✅", success_message)
            
            # 验证原消息被删除
            mock_callback.message.delete.assert_called_once()
            
            # 验证后续查询使用新语言
            user_language = await get_user_language(123456)
            self.assertEqual(user_language, 'en_US')
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_language_persistence_across_operations(self, mock_get_client):
        """
        测试语言设置在多次操作中的持久性
        """
        from module.i18n.services.i18n_manager import save_user_language_async, get_user_language
        
        # Mock MongoDB
        mock_client = AsyncMock()
        mock_db = AsyncMock()
        mock_collection = AsyncMock()
        
        mock_get_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # 第一次保存
        mock_result_save = MagicMock()
        mock_result_save.modified_count = 0
        mock_result_save.upserted_id = "new_id"
        mock_collection.update_one.return_value = mock_result_save
        
        result1 = await save_user_language_async(789012, 'zh_CN')
        self.assertTrue(result1)
        
        # 模拟查询返回保存的数据
        mock_collection.find_one.return_value = {
            'user_id': 789012,
            'language_code': 'zh_CN'
        }
        
        # Mock UserLanguage.get_user_language失败，强制使用异步查询
        with patch('beans.user_language.UserLanguage.get_user_language', return_value=None):
            language = await get_user_language(789012)
            self.assertEqual(language, 'zh_CN')
        
        # 第二次更新语言
        mock_result_update = MagicMock()
        mock_result_update.modified_count = 1
        mock_result_update.upserted_id = None
        mock_collection.update_one.return_value = mock_result_update
        
        result2 = await save_user_language_async(789012, 'en_US')
        self.assertTrue(result2)
        
        # 验证更新操作
        self.assertEqual(mock_collection.update_one.call_count, 2)
        
        # 验证最后一次调用使用了正确的语言代码
        last_call = mock_collection.update_one.call_args
        last_update_data = last_call[0][1]['$set']
        self.assertEqual(last_update_data['language_code'], 'en_US')
    
    async def test_error_handling_and_recovery(self):
        """
        测试错误处理和恢复机制
        """
        from module.i18n.services.i18n_manager import save_user_language_async
        
        # 测试数据库连接失败的情况
        with patch('tool.mongo_client.get_motor_client') as mock_get_client:
            mock_get_client.side_effect = Exception("Database connection failed")
            
            result = await save_user_language_async(123456, 'en_US')
            self.assertFalse(result)
    
    async def test_concurrent_language_operations(self):
        """
        测试并发语言操作的正确性
        """
        from module.i18n.services.i18n_manager import save_user_language_async
        
        with patch('tool.mongo_client.get_motor_client') as mock_get_client:
            # Mock MongoDB
            mock_client = AsyncMock()
            mock_db = AsyncMock()
            mock_collection = AsyncMock()
            
            mock_get_client.return_value = mock_client
            mock_client.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection
            
            # Mock成功的更新结果
            mock_result = MagicMock()
            mock_result.modified_count = 1
            mock_result.upserted_id = None
            mock_collection.update_one.return_value = mock_result
            
            # 并发执行多个保存操作
            tasks = []
            user_language_pairs = [
                (111, 'en_US'),
                (222, 'zh_CN'),
                (333, 'en_US'),
                (444, 'zh_CN')
            ]
            
            for user_id, language in user_language_pairs:
                task = save_user_language_async(user_id, language)
                tasks.append(task)
            
            # 等待所有操作完成
            results = await asyncio.gather(*tasks)
            
            # 验证所有操作都成功
            self.assertTrue(all(results))
            
            # 验证数据库被调用了正确的次数
            self.assertEqual(mock_collection.update_one.call_count, 4)
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    async def test_invalid_language_rejection(self, mock_get_i18n):
        """
        测试无效语言代码被正确拒绝
        """
        from module.i18n.commands.lang_command import handle_lang_callback
        
        # Mock i18n manager
        mock_i18n = MagicMock()
        mock_get_i18n.return_value = mock_i18n
        
        # 只支持特定语言
        mock_i18n.get_available_languages.return_value = [
            {'code': 'zh_CN', 'name': 'Chinese (Simplified)', 'native_name': '简体中文'},
            {'code': 'en_US', 'name': 'English', 'native_name': 'English'}
        ]
        
        mock_i18n.save_user_language = AsyncMock()
        mock_i18n.translate_for_user = AsyncMock(return_value="❌ 不支持的语言")
        
        # 创建无效语言的回调
        from pyrogram.types import CallbackQuery
        mock_client = AsyncMock()
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.data = "lang_invalid_lang"
        mock_callback.from_user.id = 123456
        mock_callback.answer = AsyncMock()
        
        # 执行回调处理
        await handle_lang_callback(mock_client, mock_callback)
        
        # 验证不会尝试保存无效语言
        mock_i18n.save_user_language.assert_not_called()
        
        # 验证返回错误消息
        mock_callback.answer.assert_called_once()
        error_message = mock_callback.answer.call_args[0][0]
        self.assertIn("❌", error_message)
    
    async def test_input_validation(self):
        """
        测试输入验证功能
        """
        from module.i18n.services.i18n_manager import save_user_language_async
        from beans.user_language import UserLanguage
        
        # 测试无效用户ID
        result1 = await save_user_language_async(-1, 'en_US')
        self.assertFalse(result1)
        
        result2 = await save_user_language_async(None, 'en_US')
        self.assertFalse(result2)
        
        # 测试无效语言代码
        result3 = await save_user_language_async(123456, '')
        self.assertFalse(result3)
        
        result4 = await save_user_language_async(123456, None)
        self.assertFalse(result4)
        
        # 测试同步版本的输入验证
        sync_result1 = UserLanguage.get_user_language(-1)
        self.assertEqual(sync_result1, 'zh_CN')
        
        sync_result2 = UserLanguage.get_user_language(0)
        self.assertEqual(sync_result2, 'zh_CN')


if __name__ == '__main__':
    print("=" * 70)
    print("TDD 重构阶段 - 完整语言选择流程集成测试")
    print("=" * 70)
    print("测试完整的端到端流程：")
    print("1. 用户交互 -> 数据验证 -> 数据库写入 -> 反馈")
    print("2. 数据持久化和一致性")
    print("3. 错误处理和恢复")
    print("4. 并发操作和输入验证")
    print("=" * 70)
    
    async def run_integration_tests():
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestLanguageFullFlowIntegration)
        
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
        print(f"集成测试结果：通过 {passed}，失败 {failed}")
        if failed == 0:
            print("🎉 所有集成测试通过！语言选择功能完全正常！")
        else:
            print("⚠️ 部分集成测试失败，需要进一步优化")
        print("=" * 70)
    
    asyncio.run(run_integration_tests())