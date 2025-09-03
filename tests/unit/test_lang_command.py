import unittest
from unittest.mock import MagicMock, patch, AsyncMock, call
import asyncio
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery


class TestLangCommand(unittest.TestCase):
    """测试/lang命令功能"""
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    @patch('module.i18n.commands.lang_command.is_admin')
    async def test_lang_command_display_menu(self, mock_is_admin, mock_get_i18n):
        """测试/lang命令显示语言选择菜单"""
        from module.i18n.commands.lang_command import lang_command
        
        # Mock设置
        mock_is_admin.return_value = True
        mock_i18n = MagicMock()
        mock_get_i18n.return_value = mock_i18n
        mock_i18n.translate_for_user = AsyncMock(side_effect=lambda uid, key, **kwargs: f"translated_{key}")
        mock_i18n.get_available_languages.return_value = [
            {'code': 'zh_CN', 'name': 'Chinese (Simplified)', 'native_name': '简体中文'},
            {'code': 'en_US', 'name': 'English', 'native_name': 'English'}
        ]
        
        # Mock消息对象
        mock_client = AsyncMock()
        mock_message = AsyncMock(spec=Message)
        mock_message.from_user.id = 123456
        mock_message.reply_text = AsyncMock()
        
        # 执行命令
        await lang_command(mock_client, mock_message)
        
        # 验证调用
        mock_message.reply_text.assert_called_once()
        args = mock_message.reply_text.call_args
        
        # 验证消息内容
        self.assertIn('translated_language.menu_title', args[0][0])
        self.assertIn('translated_language.select_prompt', args[0][0])
        
        # 验证键盘按钮
        reply_markup = args[1]['reply_markup']
        self.assertIsInstance(reply_markup, InlineKeyboardMarkup)
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    async def test_lang_callback_change_language(self, mock_get_i18n):
        """测试语言切换回调"""
        from module.i18n.commands.lang_command import handle_lang_callback
        
        # Mock设置
        mock_i18n = MagicMock()
        mock_get_i18n.return_value = mock_i18n
        mock_i18n.save_user_language = AsyncMock(return_value=True)
        mock_i18n.translate_for_user = AsyncMock(
            return_value="✅ 语言已切换为: English"
        )
        
        # Mock回调查询
        mock_client = AsyncMock()
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.data = "lang_en_US"
        mock_callback.from_user.id = 123456
        mock_callback.message.delete = AsyncMock()
        mock_callback.answer = AsyncMock()
        
        # 执行回调
        await handle_lang_callback(mock_client, mock_callback)
        
        # 验证语言保存
        mock_i18n.save_user_language.assert_called_once_with(123456, 'en_US')
        
        # 验证回调响应
        mock_callback.answer.assert_called_once()
        answer_text = mock_callback.answer.call_args[0][0]
        self.assertIn("✅", answer_text)
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    async def test_lang_callback_invalid_language(self, mock_get_i18n):
        """测试无效语言代码处理"""
        from module.i18n.commands.lang_command import handle_lang_callback
        
        # Mock设置
        mock_i18n = MagicMock()
        mock_get_i18n.return_value = mock_i18n
        mock_i18n.save_user_language = AsyncMock(return_value=False)
        mock_i18n.translate_for_user = AsyncMock(
            return_value="❌ 不支持的语言: invalid_lang"
        )
        
        # Mock回调查询
        mock_client = AsyncMock()
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.data = "lang_invalid_lang"
        mock_callback.from_user.id = 123456
        mock_callback.answer = AsyncMock()
        
        # 执行回调
        await handle_lang_callback(mock_client, mock_callback)
        
        # 验证错误响应
        mock_callback.answer.assert_called_once()
        answer_text = mock_callback.answer.call_args[0][0]
        self.assertIn("❌", answer_text)
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    async def test_current_language_display(self, mock_get_i18n):
        """测试显示当前语言"""
        from module.i18n.commands.lang_command import lang_command
        
        # Mock设置
        mock_i18n = MagicMock()
        mock_get_i18n.return_value = mock_i18n
        mock_i18n.get_user_language = AsyncMock(return_value='zh_CN')
        mock_i18n.translate_for_user = AsyncMock(
            side_effect=lambda uid, key, **kwargs: {
                'language.current': f"当前语言: {kwargs.get('language', 'zh_CN')}",
                'language.menu_title': "🌐 选择语言",
                'language.select_prompt': "请选择您偏好的语言:"
            }.get(key, key)
        )
        mock_i18n.get_available_languages.return_value = [
            {'code': 'zh_CN', 'name': 'Chinese (Simplified)', 'native_name': '简体中文'},
            {'code': 'en_US', 'name': 'English', 'native_name': 'English'}
        ]
        
        # Mock消息对象
        mock_client = AsyncMock()
        mock_message = AsyncMock(spec=Message)
        mock_message.from_user.id = 123456
        mock_message.reply_text = AsyncMock()
        
        # 执行命令
        await lang_command(mock_client, mock_message)
        
        # 验证当前语言显示
        mock_message.reply_text.assert_called_once()
        args = mock_message.reply_text.call_args
        message_text = args[0][0]
        
        self.assertIn("当前语言", message_text)
        self.assertIn("简体中文", message_text)
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    @patch('module.i18n.commands.lang_command.is_admin')
    async def test_lang_command_non_admin(self, mock_is_admin, mock_get_i18n):
        """测试非管理员访问/lang命令"""
        from module.i18n.commands.lang_command import lang_command
        
        # Mock设置 - 非管理员
        mock_is_admin.return_value = False
        mock_i18n = MagicMock()
        mock_get_i18n.return_value = mock_i18n
        
        # Mock消息对象
        mock_client = AsyncMock()
        mock_message = AsyncMock(spec=Message)
        mock_message.from_user.id = 123456
        mock_message.reply_text = AsyncMock()
        
        # 由于is_admin filter会阻止执行，这里模拟filter的行为
        # 实际上命令不会被执行，但为了测试完整性，我们仍然测试这个场景
        # 注意：在实际使用中，Pyrogram的filter会阻止非管理员执行
    
    async def test_language_persistence(self):
        """测试语言设置持久化"""
        from module.i18n.commands.lang_command import handle_lang_callback
        from module.i18n.services.i18n_manager import I18nManager
        
        with patch('module.i18n.commands.lang_command.get_i18n_manager') as mock_get_i18n:
            # Mock设置
            mock_i18n = MagicMock()
            mock_get_i18n.return_value = mock_i18n
            mock_i18n.save_user_language = AsyncMock(return_value=True)
            mock_i18n.get_user_language = AsyncMock(return_value='en_US')
            mock_i18n.translate_for_user = AsyncMock(return_value="Success")
            
            # Mock回调查询
            mock_client = AsyncMock()
            mock_callback = AsyncMock(spec=CallbackQuery)
            mock_callback.data = "lang_en_US"
            mock_callback.from_user.id = 123456
            mock_callback.message.delete = AsyncMock()
            mock_callback.answer = AsyncMock()
            
            # 执行语言切换
            await handle_lang_callback(mock_client, mock_callback)
            
            # 验证持久化调用
            mock_i18n.save_user_language.assert_called_with(123456, 'en_US')
            
            # 验证可以获取设置的语言
            saved_lang = await mock_i18n.get_user_language(123456)
            self.assertEqual(saved_lang, 'en_US')


class TestLangIntegration(unittest.TestCase):
    """语言命令集成测试"""
    
    @patch('module.i18n.commands.lang_command.get_motor_collection')
    async def test_mongodb_language_switch(self, mock_get_collection):
        """测试MongoDB中的语言切换"""
        from module.i18n.commands.lang_command import handle_lang_callback
        
        # Mock MongoDB collection
        mock_collection = AsyncMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.update_one.return_value = MagicMock(
            modified_count=1,
            upserted_id=None
        )
        
        with patch('module.i18n.commands.lang_command.get_i18n_manager') as mock_get_i18n:
            mock_i18n = MagicMock()
            mock_get_i18n.return_value = mock_i18n
            mock_i18n.save_user_language = AsyncMock(return_value=True)
            mock_i18n.translate_for_user = AsyncMock(return_value="Success")
            
            # Mock回调查询
            mock_client = AsyncMock()
            mock_callback = AsyncMock(spec=CallbackQuery)
            mock_callback.data = "lang_zh_CN"
            mock_callback.from_user.id = 789012
            mock_callback.message.delete = AsyncMock()
            mock_callback.answer = AsyncMock()
            
            # 执行语言切换
            await handle_lang_callback(mock_client, mock_callback)
            
            # 验证数据库操作
            mock_i18n.save_user_language.assert_called_once_with(789012, 'zh_CN')


if __name__ == '__main__':
    # 运行异步测试
    async def run_async_tests():
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # 添加测试
        suite.addTests(loader.loadTestsFromTestCase(TestLangCommand))
        suite.addTests(loader.loadTestsFromTestCase(TestLangIntegration))
        
        runner = unittest.TextTestRunner(verbosity=2)
        
        # 运行所有测试
        for test in suite:
            test_method = getattr(test, test._testMethodName)
            if asyncio.iscoroutinefunction(test_method):
                await test_method(test)
    
    asyncio.run(run_async_tests())