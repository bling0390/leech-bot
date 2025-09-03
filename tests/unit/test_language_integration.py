import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from pyrogram.types import CallbackQuery, Message


class TestLanguageIntegration(unittest.TestCase):
    """完整的语言切换集成测试"""
    
    async def test_complete_language_switch_flow(self):
        """测试完整的语言切换流程：从中文切换到英文"""
        
        # 导入必要的模块
        from module.i18n.services.i18n_manager import I18nManager
        
        # 创建i18n管理器实例
        i18n = I18nManager()
        
        # 模拟用户ID
        user_id = 888888
        
        # 第一步：验证初始状态（默认中文）
        with patch('module.i18n.services.i18n_manager.get_user_language') as mock_get_lang:
            mock_get_lang.return_value = asyncio.coroutine(lambda user_id: 'zh_CN')()
            
            # 获取中文消息
            chinese_msg = i18n.translate('disk.monitor.started', locale='zh_CN')
            self.assertEqual(chinese_msg, '✅ 磁盘监控已启动')
        
        # 第二步：模拟用户点击/lang命令
        from module.i18n.commands.lang_command import lang_command
        
        with patch('module.i18n.commands.lang_command.get_i18n_manager') as mock_get_i18n:
            mock_get_i18n.return_value = i18n
            
            # 创建消息对象
            mock_client = AsyncMock()
            mock_message = AsyncMock(spec=Message)
            mock_message.from_user.id = user_id
            mock_message.reply_text = AsyncMock()
            
            # 执行/lang命令
            await lang_command(mock_client, mock_message)
            
            # 验证显示了语言选择菜单
            mock_message.reply_text.assert_called_once()
            call_args = mock_message.reply_text.call_args
            
            # 验证菜单中包含语言选择选项
            self.assertIn('reply_markup', call_args[1])
            reply_markup = call_args[1]['reply_markup']
            
            # 获取按钮文本
            buttons = []
            for row in reply_markup.inline_keyboard:
                for button in row:
                    buttons.append((button.text, button.callback_data))
            
            # 验证包含English选项
            english_button = next((b for b in buttons if 'English' in b[0]), None)
            self.assertIsNotNone(english_button)
            self.assertEqual(english_button[1], 'lang_en_US')
        
        # 第三步：模拟用户点击English按钮
        from module.i18n.commands.lang_command import handle_lang_callback
        
        with patch('module.i18n.commands.lang_command.get_i18n_manager') as mock_get_i18n:
            mock_i18n = MagicMock()
            mock_get_i18n.return_value = mock_i18n
            
            # 设置Mock行为
            mock_i18n.get_available_languages.return_value = [
                {'code': 'zh_CN', 'name': 'Chinese (Simplified)', 'native_name': '简体中文'},
                {'code': 'en_US', 'name': 'English', 'native_name': 'English'}
            ]
            mock_i18n.save_user_language = AsyncMock(return_value=True)
            mock_i18n.translate_for_user = AsyncMock(return_value='✅ Language changed to: English')
            
            # 创建回调查询
            mock_callback = AsyncMock(spec=CallbackQuery)
            mock_callback.data = 'lang_en_US'
            mock_callback.from_user.id = user_id
            mock_callback.message.delete = AsyncMock()
            mock_callback.answer = AsyncMock()
            
            # 执行回调
            await handle_lang_callback(mock_client, mock_callback)
            
            # 验证语言已保存
            mock_i18n.save_user_language.assert_called_once_with(user_id, 'en_US')
            
            # 验证成功消息
            mock_callback.answer.assert_called_once()
            answer_text = mock_callback.answer.call_args[0][0]
            self.assertIn('✅', answer_text)
            self.assertIn('English', answer_text)
        
        # 第四步：验证后续消息使用英文
        with patch('module.i18n.services.i18n_manager.get_user_language') as mock_get_lang:
            mock_get_lang.return_value = asyncio.coroutine(lambda user_id: 'en_US')()
            
            # 获取英文消息
            english_msg = i18n.translate('disk.monitor.started', locale='en_US')
            self.assertEqual(english_msg, '✅ Disk monitor started')
            
            # 验证不同的消息也是英文
            english_status = i18n.translate('disk.status.title', locale='en_US')
            self.assertEqual(english_status, '📊 Disk Status Report')
    
    async def test_language_persistence_across_sessions(self):
        """测试语言设置在会话间的持久性"""
        
        from module.i18n.services.i18n_manager import save_user_language_async, get_user_language
        
        user_id = 999999
        
        # 模拟保存语言设置
        with patch('module.i18n.services.i18n_manager.get_motor_client') as mock_get_client:
            mock_client = MagicMock()
            mock_db = MagicMock()
            mock_collection = AsyncMock()
            
            mock_get_client.return_value = mock_client
            mock_client.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection
            
            # 模拟更新成功
            mock_collection.update_one.return_value = MagicMock(
                modified_count=1,
                upserted_id=None
            )
            
            # 保存英文设置
            result = await save_user_language_async(user_id, 'en_US')
            self.assertTrue(result)
            
            # 验证调用了正确的更新
            mock_collection.update_one.assert_called_once()
            call_args = mock_collection.update_one.call_args[0]
            self.assertEqual(call_args[0], {'user_id': user_id})
            self.assertEqual(call_args[1]['$set']['language_code'], 'en_US')
        
        # 模拟获取语言设置
        with patch('module.i18n.services.i18n_manager.get_motor_client') as mock_get_client:
            mock_client = MagicMock()
            mock_db = MagicMock()
            mock_collection = AsyncMock()
            
            mock_get_client.return_value = mock_client
            mock_client.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection
            
            # 模拟找到用户语言设置
            mock_collection.find_one.return_value = {
                'user_id': user_id,
                'language_code': 'en_US'
            }
            
            # 获取语言
            language = await get_user_language(user_id)
            self.assertEqual(language, 'en_US')
    
    async def test_invalid_language_handling(self):
        """测试处理无效语言代码"""
        
        from module.i18n.commands.lang_command import handle_lang_callback
        
        with patch('module.i18n.commands.lang_command.get_i18n_manager') as mock_get_i18n:
            mock_i18n = MagicMock()
            mock_get_i18n.return_value = mock_i18n
            
            # 设置可用语言
            mock_i18n.get_available_languages.return_value = [
                {'code': 'zh_CN', 'name': 'Chinese (Simplified)', 'native_name': '简体中文'},
                {'code': 'en_US', 'name': 'English', 'native_name': 'English'}
            ]
            
            mock_i18n.translate_for_user = AsyncMock(return_value='❌ 不支持的语言: fr_FR')
            
            # 创建回调查询，使用无效语言
            mock_client = AsyncMock()
            mock_callback = AsyncMock(spec=CallbackQuery)
            mock_callback.data = 'lang_fr_FR'  # 不支持的语言
            mock_callback.from_user.id = 123456
            mock_callback.answer = AsyncMock()
            
            # 执行回调
            await handle_lang_callback(mock_client, mock_callback)
            
            # 验证显示错误消息
            mock_callback.answer.assert_called_once()
            call_args = mock_callback.answer.call_args
            self.assertTrue(call_args[1]['show_alert'])  # 应该显示警告框


if __name__ == '__main__':
    async def run_integration_tests():
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestLanguageIntegration)
        runner = unittest.TextTestRunner(verbosity=2)
        
        print("=" * 60)
        print("运行语言切换集成测试")
        print("=" * 60)
        
        for test in suite:
            test_method = getattr(test, test._testMethodName)
            if asyncio.iscoroutinefunction(test_method):
                try:
                    await test_method(test)
                    print(f"✅ {test._testMethodName} 通过")
                except AssertionError as e:
                    print(f"❌ {test._testMethodName} 失败: {e}")
                except Exception as e:
                    print(f"❌ {test._testMethodName} 错误: {e}")
    
    asyncio.run(run_integration_tests())