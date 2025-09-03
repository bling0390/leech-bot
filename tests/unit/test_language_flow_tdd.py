"""
TDD 红灯阶段：测试语言选择功能的完整流程

测试从用户点击语言按钮到数据库写入的完整流程，
确保每一步都按预期工作并正确写入 user_language 表。
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup


class TestLanguageFlowTDD(unittest.TestCase):
    """TDD 红灯阶段：完整语言选择流程测试"""
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    async def test_complete_language_switch_flow_should_write_to_database(self, mock_get_i18n):
        """
        失败测试：完整的语言切换流程应该正确写入数据库
        
        测试流程：
        1. 用户点击 English 按钮
        2. 验证语言代码
        3. 保存到 user_language 表
        4. 返回成功消息
        5. 后续消息使用新语言
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
        
        # Mock 保存成功 - 这里会失败因为实际实现有问题
        mock_i18n.save_user_language = AsyncMock(return_value=True)
        mock_i18n.translate_for_user = AsyncMock(return_value="✅ Language changed to: English")
        
        # 创建回调查询
        mock_client = AsyncMock()
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.data = "lang_en_US"
        mock_callback.from_user.id = 123456
        mock_callback.message.delete = AsyncMock()
        mock_callback.answer = AsyncMock()
        
        # 执行完整流程
        await handle_lang_callback(mock_client, mock_callback)
        
        # 验证步骤 1: 语言代码验证
        mock_i18n.get_available_languages.assert_called_once()
        
        # 验证步骤 2: 保存到数据库 - 关键测试点
        mock_i18n.save_user_language.assert_called_once_with(123456, 'en_US')
        
        # 验证步骤 3: 用户收到成功反馈
        mock_callback.answer.assert_called_once()
        success_message = mock_callback.answer.call_args[0][0]
        self.assertIn("✅", success_message)
        
        # 验证步骤 4: 原消息被删除（表示操作成功）
        mock_callback.message.delete.assert_called_once()
        
        # 关键验证：确保实际调用了正确的保存方法
        self.assertTrue(mock_i18n.save_user_language.called,
                       "语言选择流程必须调用 save_user_language 方法")
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    @patch('beans.user_language.UserLanguage.set_user_language')
    async def test_language_persistence_in_user_language_table(self, mock_set_user_lang, mock_get_i18n):
        """
        失败测试：验证语言偏好确实写入了 user_language 表
        
        直接测试底层的数据库写入操作
        """
        from module.i18n.commands.lang_command import handle_lang_callback
        from module.i18n.services.i18n_manager import save_user_language_async
        
        # Mock UserLanguage.set_user_language
        mock_set_user_lang.return_value = True
        
        # Mock i18n manager
        mock_i18n = MagicMock()
        mock_get_i18n.return_value = mock_i18n
        mock_i18n.get_available_languages.return_value = [
            {'code': 'zh_CN', 'name': 'Chinese (Simplified)', 'native_name': '简体中文'},
            {'code': 'en_US', 'name': 'English', 'native_name': 'English'}
        ]
        
        # 重要：确保 save_user_language 调用底层的 UserLanguage 方法
        async def mock_save_user_language(user_id, language):
            # 这里应该调用 UserLanguage.set_user_language
            return mock_set_user_lang(user_id, language)
        
        mock_i18n.save_user_language = mock_save_user_language
        mock_i18n.translate_for_user = AsyncMock(return_value="Success")
        
        # 创建回调查询
        mock_client = AsyncMock()
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.data = "lang_zh_CN"
        mock_callback.from_user.id = 789012
        mock_callback.message.delete = AsyncMock()
        mock_callback.answer = AsyncMock()
        
        # 执行语言切换
        await handle_lang_callback(mock_client, mock_callback)
        
        # 关键验证：确保调用了 UserLanguage.set_user_language
        mock_set_user_lang.assert_called_once_with(789012, 'zh_CN')
        
        # 这个测试可能会失败，因为实际实现可能没有正确调用 UserLanguage
    
    @patch('tool.mongo_client.get_motor_client')
    async def test_database_record_should_match_user_language_schema(self, mock_get_client):
        """
        失败测试：数据库记录应该符合 UserLanguage 模型的模式
        
        验证写入数据库的记录格式与 UserLanguage 模型定义一致
        """
        from module.i18n.services.i18n_manager import save_user_language_async
        from beans.user_language import UserLanguage
        
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
        
        # 执行保存操作
        await save_user_language_async(123456, 'en_US')
        
        # 获取实际调用的参数
        update_call = mock_collection.update_one.call_args
        filter_dict = update_call[0][0]
        update_dict = update_call[0][1]
        
        # 验证过滤条件使用正确的字段名
        self.assertIn('user_id', filter_dict,
                     "查询过滤条件应该使用 'user_id' 字段")
        
        # 验证更新数据包含必要字段
        set_data = update_dict['$set']
        self.assertIn('user_id', set_data,
                     "更新数据应该包含 'user_id' 字段")
        self.assertIn('language_code', set_data,
                     "更新数据应该包含 'language_code' 字段")
        
        # 验证数据类型
        self.assertIsInstance(set_data['user_id'], int,
                            "user_id 应该是整数类型")
        self.assertIsInstance(set_data['language_code'], str,
                            "language_code 应该是字符串类型")
        
        # 验证使用的集合名称与模型定义一致
        expected_collection = UserLanguage._meta['collection']
        actual_collection = mock_db.__getitem__.call_args[0][0]
        self.assertEqual(actual_collection, expected_collection,
                        f"应该使用 '{expected_collection}' 集合，实际使用了 '{actual_collection}'")
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    async def test_invalid_language_should_not_write_to_database(self, mock_get_i18n):
        """
        失败测试：无效语言代码不应该写入数据库
        
        测试输入验证功能，确保只有有效语言才被保存
        """
        from module.i18n.commands.lang_command import handle_lang_callback
        
        # Mock i18n manager
        mock_i18n = MagicMock()
        mock_get_i18n.return_value = mock_i18n
        
        # Mock 只支持特定语言
        mock_i18n.get_available_languages.return_value = [
            {'code': 'zh_CN', 'name': 'Chinese (Simplified)', 'native_name': '简体中文'},
            {'code': 'en_US', 'name': 'English', 'native_name': 'English'}
        ]
        
        # Mock 翻译错误消息
        mock_i18n.translate_for_user = AsyncMock(return_value="❌ 不支持的语言")
        mock_i18n.save_user_language = AsyncMock()
        
        # 创建无效语言的回调查询
        mock_client = AsyncMock()
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.data = "lang_invalid_language"
        mock_callback.from_user.id = 123456
        mock_callback.answer = AsyncMock()
        
        # 执行回调处理
        await handle_lang_callback(mock_client, mock_callback)
        
        # 验证：无效语言不应该被保存
        mock_i18n.save_user_language.assert_not_called()
        
        # 验证：用户应该收到错误消息
        mock_callback.answer.assert_called_once()
        error_message = mock_callback.answer.call_args[0][0]
        self.assertIn("❌", error_message)
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    async def test_concurrent_language_switches_should_be_handled_correctly(self, mock_get_i18n):
        """
        失败测试：并发语言切换应该被正确处理
        
        测试多个用户同时切换语言的情况
        """
        from module.i18n.commands.lang_command import handle_lang_callback
        
        # Mock i18n manager
        mock_i18n = MagicMock()
        mock_get_i18n.return_value = mock_i18n
        
        mock_i18n.get_available_languages.return_value = [
            {'code': 'zh_CN', 'name': 'Chinese (Simplified)', 'native_name': '简体中文'},
            {'code': 'en_US', 'name': 'English', 'native_name': 'English'}
        ]
        
        # 记录保存调用
        save_calls = []
        
        async def mock_save_user_language(user_id, language):
            save_calls.append((user_id, language))
            return True
        
        mock_i18n.save_user_language = mock_save_user_language
        mock_i18n.translate_for_user = AsyncMock(return_value="Success")
        
        # 创建多个并发回调查询
        tasks = []
        for i, (user_id, lang) in enumerate([(111, 'en_US'), (222, 'zh_CN'), (333, 'en_US')]):
            mock_client = AsyncMock()
            mock_callback = AsyncMock(spec=CallbackQuery)
            mock_callback.data = f"lang_{lang}"
            mock_callback.from_user.id = user_id
            mock_callback.message.delete = AsyncMock()
            mock_callback.answer = AsyncMock()
            
            tasks.append(handle_lang_callback(mock_client, mock_callback))
        
        # 并发执行
        await asyncio.gather(*tasks)
        
        # 验证：每个用户的语言都应该被正确保存
        expected_calls = [(111, 'en_US'), (222, 'zh_CN'), (333, 'en_US')]
        self.assertEqual(len(save_calls), 3,
                        f"应该有3次保存调用，实际有{len(save_calls)}次")
        
        for expected_call in expected_calls:
            self.assertIn(expected_call, save_calls,
                         f"缺少保存调用: {expected_call}")
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    async def test_language_switch_should_update_existing_record(self, mock_get_i18n):
        """
        失败测试：语言切换应该更新现有记录而不是创建重复记录
        
        测试用户已有语言记录时的更新行为
        """
        from module.i18n.commands.lang_command import handle_lang_callback
        
        # Mock i18n manager
        mock_i18n = MagicMock()
        mock_get_i18n.return_value = mock_i18n
        
        mock_i18n.get_available_languages.return_value = [
            {'code': 'zh_CN', 'name': 'Chinese (Simplified)', 'native_name': '简体中文'},
            {'code': 'en_US', 'name': 'English', 'native_name': 'English'}
        ]
        
        # 模拟现有用户首先设置中文
        mock_i18n.save_user_language = AsyncMock(return_value=True)
        mock_i18n.translate_for_user = AsyncMock(return_value="Success")
        
        # 第一次设置中文
        mock_client = AsyncMock()
        mock_callback1 = AsyncMock(spec=CallbackQuery)
        mock_callback1.data = "lang_zh_CN"
        mock_callback1.from_user.id = 123456
        mock_callback1.message.delete = AsyncMock()
        mock_callback1.answer = AsyncMock()
        
        await handle_lang_callback(mock_client, mock_callback1)
        
        # 第二次切换为英文
        mock_callback2 = AsyncMock(spec=CallbackQuery)
        mock_callback2.data = "lang_en_US"
        mock_callback2.from_user.id = 123456  # 同一用户
        mock_callback2.message.delete = AsyncMock()
        mock_callback2.answer = AsyncMock()
        
        await handle_lang_callback(mock_client, mock_callback2)
        
        # 验证：save_user_language 应该被调用两次（中文一次，英文一次）
        self.assertEqual(mock_i18n.save_user_language.call_count, 2,
                        "用户切换语言应该调用两次保存操作")
        
        # 验证：第二次调用使用正确的语言代码
        second_call = mock_i18n.save_user_language.call_args
        self.assertEqual(second_call[0][0], 123456, "用户ID应该正确")
        self.assertEqual(second_call[0][1], 'en_US', "语言代码应该是 en_US")


if __name__ == '__main__':
    print("=" * 60)
    print("TDD 红灯阶段 - 完整语言选择流程测试")
    print("=" * 60)
    print("测试完整的语言切换流程，包括：")
    print("1. 用户交互 -> 数据验证 -> 数据库写入")
    print("2. 数据持久化和一致性")
    print("3. 并发处理和错误处理")
    print("=" * 60)
    
    async def run_flow_tests():
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestLanguageFlowTDD)
        
        for test in suite:
            test_method = getattr(test, test._testMethodName)
            if asyncio.iscoroutinefunction(test_method):
                try:
                    await test_method(test)
                    print(f"🟢 {test._testMethodName} - 通过")
                except AssertionError as e:
                    print(f"🔴 {test._testMethodName} - 失败: {str(e)[:100]}...")
                except Exception as e:
                    print(f"❌ {test._testMethodName} - 错误: {str(e)[:100]}...")
    
    asyncio.run(run_flow_tests())