import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from pyrogram.types import CallbackQuery


class TestLanguageSwitchFix(unittest.TestCase):
    """测试语言切换修复 - TDD红灯阶段"""
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    async def test_english_button_should_work(self, mock_get_i18n):
        """测试点击English按钮应该成功切换语言"""
        from module.i18n.commands.lang_command import handle_lang_callback
        
        # 设置Mock
        mock_i18n = MagicMock()
        mock_get_i18n.return_value = mock_i18n
        
        # 模拟返回可用语言列表
        mock_i18n.get_available_languages.return_value = [
            {'code': 'zh_CN', 'name': 'Chinese (Simplified)', 'native_name': '简体中文'},
            {'code': 'en_US', 'name': 'English', 'native_name': 'English'}
        ]
        
        # 模拟保存语言成功
        mock_i18n.save_user_language = AsyncMock(return_value=True)
        mock_i18n.translate_for_user = AsyncMock(return_value="✅ Language changed to: English")
        
        # 创建回调查询
        mock_client = AsyncMock()
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.data = "lang_en_US"  # 用户点击English按钮
        mock_callback.from_user.id = 123456
        mock_callback.message.delete = AsyncMock()
        mock_callback.answer = AsyncMock()
        
        # 执行回调处理
        await handle_lang_callback(mock_client, mock_callback)
        
        # 验证：应该成功保存语言，而不是报错"不支持的语言"
        mock_i18n.save_user_language.assert_called_once_with(123456, 'en_US')
        
        # 验证：应该显示成功消息，而不是错误消息
        mock_callback.answer.assert_called_once()
        answer_args = mock_callback.answer.call_args[0][0]
        self.assertIn("✅", answer_args)
        self.assertNotIn("不支持的语言", answer_args)
        self.assertNotIn("Unsupported", answer_args)
        
        # 验证：消息应该被删除（表示操作成功）
        mock_callback.message.delete.assert_called_once()
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    async def test_chinese_button_should_work(self, mock_get_i18n):
        """测试点击中文按钮应该成功切换语言"""
        from module.i18n.commands.lang_command import handle_lang_callback
        
        # 设置Mock
        mock_i18n = MagicMock()
        mock_get_i18n.return_value = mock_i18n
        
        # 模拟返回可用语言列表
        mock_i18n.get_available_languages.return_value = [
            {'code': 'zh_CN', 'name': 'Chinese (Simplified)', 'native_name': '简体中文'},
            {'code': 'en_US', 'name': 'English', 'native_name': 'English'}
        ]
        
        # 模拟保存语言成功
        mock_i18n.save_user_language = AsyncMock(return_value=True)
        mock_i18n.translate_for_user = AsyncMock(return_value="✅ 语言已切换为: 简体中文")
        
        # 创建回调查询
        mock_client = AsyncMock()
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.data = "lang_zh_CN"  # 用户点击中文按钮
        mock_callback.from_user.id = 123456
        mock_callback.message.delete = AsyncMock()
        mock_callback.answer = AsyncMock()
        
        # 执行回调处理
        await handle_lang_callback(mock_client, mock_callback)
        
        # 验证：应该成功保存语言
        mock_i18n.save_user_language.assert_called_once_with(123456, 'zh_CN')
        
        # 验证：应该显示成功消息
        mock_callback.answer.assert_called_once()
        answer_args = mock_callback.answer.call_args[0][0]
        self.assertIn("✅", answer_args)
        
        # 验证：消息应该被删除
        mock_callback.message.delete.assert_called_once()
    
    @patch('module.i18n.commands.lang_command.get_i18n_manager')
    @patch('module.disk.commands.disk_command.get_i18n_manager')
    async def test_messages_after_language_switch(self, mock_disk_i18n, mock_lang_i18n):
        """测试切换到英文后，后续消息应该使用英文"""
        from module.i18n.commands.lang_command import handle_lang_callback
        
        # 设置语言命令的Mock
        mock_i18n = MagicMock()
        mock_lang_i18n.return_value = mock_i18n
        mock_disk_i18n.return_value = mock_i18n
        
        # 模拟返回可用语言列表
        mock_i18n.get_available_languages.return_value = [
            {'code': 'zh_CN', 'name': 'Chinese (Simplified)', 'native_name': '简体中文'},
            {'code': 'en_US', 'name': 'English', 'native_name': 'English'}
        ]
        
        # 模拟保存语言成功
        mock_i18n.save_user_language = AsyncMock(return_value=True)
        mock_i18n.get_user_language = AsyncMock(return_value='en_US')
        
        # 模拟翻译函数，根据语言返回对应文本
        async def mock_translate(user_id, key, **kwargs):
            # 获取用户语言
            user_lang = await mock_i18n.get_user_language(user_id)
            if user_lang == 'en_US':
                translations = {
                    'language.changed': '✅ Language changed to: English',
                    'disk.monitor.started': '✅ Disk monitor started',
                    'disk.status.title': '📊 Disk Status Report'
                }
            else:
                translations = {
                    'language.changed': '✅ 语言已切换为: 简体中文',
                    'disk.monitor.started': '✅ 磁盘监控已启动',
                    'disk.status.title': '📊 磁盘状态报告'
                }
            return translations.get(key, key)
        
        mock_i18n.translate_for_user = mock_translate
        
        # 创建回调查询切换到英文
        mock_client = AsyncMock()
        mock_callback = AsyncMock(spec=CallbackQuery)
        mock_callback.data = "lang_en_US"
        mock_callback.from_user.id = 123456
        mock_callback.message.delete = AsyncMock()
        mock_callback.answer = AsyncMock()
        
        # 执行语言切换
        await handle_lang_callback(mock_client, mock_callback)
        
        # 验证语言已保存为英文
        mock_i18n.save_user_language.assert_called_with(123456, 'en_US')
        
        # 模拟后续的磁盘监控消息
        disk_message = await mock_i18n.translate_for_user(123456, 'disk.monitor.started')
        self.assertEqual(disk_message, '✅ Disk monitor started')
        self.assertNotEqual(disk_message, '✅ 磁盘监控已启动')
        
        # 模拟磁盘状态消息
        status_message = await mock_i18n.translate_for_user(123456, 'disk.status.title')
        self.assertEqual(status_message, '📊 Disk Status Report')
        self.assertNotEqual(status_message, '📊 磁盘状态报告')
    
    async def test_language_code_validation(self):
        """测试语言代码验证逻辑"""
        # 测试场景：验证 en_US 应该在有效代码列表中
        available_languages = [
            {'code': 'zh_CN', 'name': 'Chinese (Simplified)', 'native_name': '简体中文'},
            {'code': 'en_US', 'name': 'English', 'native_name': 'English'}
        ]
        
        # 提取有效代码
        valid_codes = [lang['code'] for lang in available_languages]
        
        # 验证 en_US 应该是有效的
        self.assertIn('en_US', valid_codes)
        self.assertIn('zh_CN', valid_codes)
        
        # 验证无效代码
        self.assertNotIn('fr_FR', valid_codes)
        self.assertNotIn('invalid_lang', valid_codes)


if __name__ == '__main__':
    # 运行异步测试
    async def run_tests():
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestLanguageSwitchFix)
        runner = unittest.TextTestRunner(verbosity=2)
        
        for test in suite:
            test_method = getattr(test, test._testMethodName)
            if asyncio.iscoroutinefunction(test_method):
                try:
                    await test_method(test)
                    print(f"✅ {test._testMethodName} passed")
                except AssertionError as e:
                    print(f"❌ {test._testMethodName} failed: {e}")
                except Exception as e:
                    print(f"❌ {test._testMethodName} error: {e}")
    
    print("=" * 60)
    print("TDD 红灯阶段 - 运行失败的测试用例")
    print("=" * 60)
    asyncio.run(run_tests())