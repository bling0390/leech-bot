import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from pathlib import Path


class TestI18nManager(unittest.TestCase):
    """测试I18n管理器的功能"""
    
    def setUp(self):
        """设置测试环境"""
        from module.i18n.services.i18n_manager import I18nManager
        self.i18n_manager = I18nManager()
    
    def test_i18n_manager_initialization(self):
        """测试I18n管理器初始化"""
        from module.i18n.services.i18n_manager import I18nManager
        manager = I18nManager()
        
        # 验证默认语言设置
        self.assertEqual(manager.default_language, 'zh_CN')
        self.assertIn('zh_CN', manager.available_languages)
        self.assertIn('en_US', manager.available_languages)
    
    def test_translate_basic(self):
        """测试基本翻译功能"""
        # 测试中文翻译
        result = self.i18n_manager.translate('disk.monitor.status', locale='zh_CN')
        self.assertIsNotNone(result)
        self.assertNotEqual(result, 'disk.monitor.status')
        
        # 测试英文翻译
        result = self.i18n_manager.translate('disk.monitor.status', locale='en_US')
        self.assertIsNotNone(result)
        self.assertNotEqual(result, 'disk.monitor.status')
    
    def test_translate_with_params(self):
        """测试带参数的翻译"""
        params = {'location': '/downloads', 'space': '10GB'}
        result = self.i18n_manager.translate(
            'disk.space_warning', 
            locale='zh_CN',
            **params
        )
        self.assertIn('/downloads', result)
        self.assertIn('10GB', result)
    
    def test_translate_missing_key(self):
        """测试翻译不存在的key"""
        result = self.i18n_manager.translate('non.existent.key', locale='zh_CN')
        # 应该返回key本身或默认值
        self.assertEqual(result, 'non.existent.key')
    
    def test_translate_invalid_locale(self):
        """测试无效的语言代码"""
        # 应该使用默认语言
        result = self.i18n_manager.translate('disk.monitor.status', locale='invalid_locale')
        self.assertIsNotNone(result)
        self.assertNotEqual(result, 'disk.monitor.status')
    
    async def test_translate_for_user(self):
        """测试基于用户的翻译"""
        from module.i18n.services.i18n_manager import I18nManager
        manager = I18nManager()
        
        # Mock用户语言偏好
        with patch('module.i18n.services.i18n_manager.get_user_language') as mock_get_lang:
            mock_get_lang.return_value = 'en_US'
            
            result = await manager.translate_for_user(123456, 'disk.monitor.status')
            self.assertIsNotNone(result)
            mock_get_lang.assert_called_once_with(123456)
    
    def test_get_available_languages(self):
        """测试获取可用语言列表"""
        languages = self.i18n_manager.get_available_languages()
        
        self.assertIsInstance(languages, list)
        self.assertGreaterEqual(len(languages), 2)
        
        # 验证返回的语言信息格式
        for lang in languages:
            self.assertIn('code', lang)
            self.assertIn('name', lang)
            self.assertIn('native_name', lang)
        
        # 验证包含中文和英文
        lang_codes = [lang['code'] for lang in languages]
        self.assertIn('zh_CN', lang_codes)
        self.assertIn('en_US', lang_codes)
    
    def test_set_user_language(self):
        """测试设置用户语言"""
        with patch('module.i18n.services.i18n_manager.save_user_language') as mock_save:
            mock_save.return_value = True
            
            result = self.i18n_manager.set_user_language(123456, 'en_US')
            self.assertTrue(result)
            mock_save.assert_called_once_with(123456, 'en_US')
    
    def test_set_invalid_language(self):
        """测试设置无效语言"""
        result = self.i18n_manager.set_user_language(123456, 'invalid_lang')
        self.assertFalse(result)
    
    def test_reload_translations(self):
        """测试重新加载翻译文件"""
        # 初始翻译
        initial_result = self.i18n_manager.translate('disk.monitor.status', locale='zh_CN')
        
        # 重新加载
        self.i18n_manager.reload_translations()
        
        # 验证翻译仍然有效
        reload_result = self.i18n_manager.translate('disk.monitor.status', locale='zh_CN')
        self.assertEqual(initial_result, reload_result)
    
    def test_pluralization(self):
        """测试复数形式处理"""
        # 测试单数
        result = self.i18n_manager.translate(
            'disk.files_count',
            locale='en_US',
            count=1
        )
        self.assertIn('file', result.lower())
        self.assertNotIn('files', result.lower())
        
        # 测试复数
        result = self.i18n_manager.translate(
            'disk.files_count',
            locale='en_US',
            count=5
        )
        self.assertIn('files', result.lower())
    
    def test_fallback_language(self):
        """测试语言回退机制"""
        # 当某个翻译在指定语言中不存在时，应该回退到默认语言
        with patch.object(self.i18n_manager, '_get_translation') as mock_trans:
            mock_trans.side_effect = [None, "默认翻译"]
            
            result = self.i18n_manager.translate('some.key', locale='en_US')
            self.assertEqual(result, "默认翻译")
            self.assertEqual(mock_trans.call_count, 2)
    
    def test_language_file_loading(self):
        """测试语言文件加载"""
        # 验证语言文件被正确加载
        self.assertTrue(self.i18n_manager.is_language_loaded('zh_CN'))
        self.assertTrue(self.i18n_manager.is_language_loaded('en_US'))
        self.assertFalse(self.i18n_manager.is_language_loaded('fr_FR'))
    
    def test_format_message_with_html(self):
        """测试HTML格式化消息"""
        result = self.i18n_manager.format_message(
            'disk.alert_template',
            locale='zh_CN',
            location='/downloads',
            free_space='5GB',
            used_percent=95
        )
        # 验证包含HTML标签
        self.assertIn('<b>', result)
        self.assertIn('</b>', result)
    
    def tearDown(self):
        """清理测试环境"""
        pass


class TestI18nIntegration(unittest.TestCase):
    """测试I18n集成功能"""
    
    @patch('module.i18n.services.i18n_manager.get_motor_collection')
    async def test_mongodb_language_persistence(self, mock_get_collection):
        """测试MongoDB语言持久化"""
        from module.i18n.services.i18n_manager import I18nManager
        
        # Mock MongoDB collection
        mock_collection = AsyncMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.find_one.return_value = {'user_id': 123456, 'language': 'en_US'}
        
        manager = I18nManager()
        
        # 测试获取用户语言
        language = await manager.get_user_language(123456)
        self.assertEqual(language, 'en_US')
        
        # 测试保存用户语言
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        result = await manager.save_user_language(123456, 'zh_CN')
        self.assertTrue(result)
        
        mock_collection.update_one.assert_called_once()
    
    async def test_concurrent_translations(self):
        """测试并发翻译请求"""
        from module.i18n.services.i18n_manager import I18nManager
        manager = I18nManager()
        
        # 创建多个并发翻译任务
        tasks = []
        for i in range(10):
            locale = 'zh_CN' if i % 2 == 0 else 'en_US'
            task = manager.translate_async('disk.monitor.status', locale=locale)
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks)
        
        # 验证所有结果都有效
        for result in results:
            self.assertIsNotNone(result)
            self.assertNotEqual(result, 'disk.monitor.status')


if __name__ == '__main__':
    # 运行同步测试
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # 运行异步测试
    async def run_async_tests():
        suite = unittest.TestLoader().loadTestsFromTestCase(TestI18nIntegration)
        runner = unittest.TextTestRunner(verbosity=2)
        
        for test in suite:
            if asyncio.iscoroutinefunction(test._testMethodName):
                await test.debug()
    
    asyncio.run(run_async_tests())