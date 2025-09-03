import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio


class TestI18nIntegration(unittest.TestCase):
    """测试i18n与现有系统的集成"""
    
    @patch('module.i18n.get_i18n_manager')
    async def test_lang_command_integration(self, mock_get_i18n):
        """测试/lang命令完整集成"""
        # 这个测试是通过导入命令来验证模块结构正确
        try:
            from module.i18n.commands.lang_command import lang_command, handle_lang_callback
            self.assertTrue(callable(lang_command))
            self.assertTrue(callable(handle_lang_callback))
        except ImportError as e:
            self.fail(f"导入lang命令失败: {e}")
    
    async def test_i18n_manager_singleton(self):
        """测试i18n管理器单例模式"""
        from module.i18n import get_i18n_manager
        
        manager1 = get_i18n_manager()
        manager2 = get_i18n_manager()
        
        # 验证是同一个实例
        self.assertIs(manager1, manager2)
    
    async def test_language_files_structure(self):
        """测试语言文件结构完整性"""
        from module.i18n.services.i18n_manager import I18nManager
        
        manager = I18nManager()
        
        # 验证中文翻译
        zh_result = manager.translate('disk.monitor.status', locale='zh_CN')
        self.assertNotEqual(zh_result, 'disk.monitor.status')
        self.assertIn('磁盘', zh_result)
        
        # 验证英文翻译
        en_result = manager.translate('disk.monitor.status', locale='en_US')
        self.assertNotEqual(en_result, 'disk.monitor.status')
        self.assertIn('Disk', en_result)
        
        # 验证两种语言不同
        self.assertNotEqual(zh_result, en_result)
    
    async def test_disk_monitor_translation_keys(self):
        """测试磁盘监控相关的翻译key"""
        from module.i18n.services.i18n_manager import I18nManager
        
        manager = I18nManager()
        
        # 测试关键翻译key存在
        important_keys = [
            'disk.monitor.status',
            'disk.monitor.started', 
            'disk.monitor.stopped',
            'disk.status.title',
            'disk.clean.complete',
            'language.menu_title',
            'language.changed',
            'common.success',
            'common.failure'
        ]
        
        for key in important_keys:
            zh_result = manager.translate(key, locale='zh_CN')
            en_result = manager.translate(key, locale='en_US')
            
            # 验证翻译存在且不是key本身
            self.assertNotEqual(zh_result, key, f"中文翻译缺失: {key}")
            self.assertNotEqual(en_result, key, f"英文翻译缺失: {key}")
            
            # 验证翻译不为空
            self.assertIsNotNone(zh_result)
            self.assertIsNotNone(en_result)
            self.assertNotEqual(zh_result.strip(), "")
            self.assertNotEqual(en_result.strip(), "")
    
    async def test_user_language_persistence_flow(self):
        """测试完整的用户语言持久化流程"""
        from module.i18n.services.i18n_manager import I18nManager, save_user_language_async, get_user_language
        
        user_id = 999999  # 测试用户ID
        
        with patch('module.i18n.services.i18n_manager.get_motor_client') as mock_motor:
            # Mock MongoDB操作
            mock_client = AsyncMock()
            mock_motor.return_value = mock_client
            mock_db = mock_client['bot']
            mock_collection = mock_db['lang']
            
            # 设置Mock行为
            mock_collection.update_one.return_value = MagicMock(
                modified_count=1,
                upserted_id=None
            )
            mock_collection.find_one.return_value = {'user_id': user_id, 'language': 'en_US'}
            
            # 测试保存语言
            result = await save_user_language_async(user_id, 'en_US')
            self.assertTrue(result)
            
            # 测试获取语言
            language = await get_user_language(user_id)
            self.assertEqual(language, 'en_US')
    
    async def test_fallback_mechanism(self):
        """测试语言回退机制"""
        from module.i18n.services.i18n_manager import I18nManager
        
        manager = I18nManager()
        
        # 测试不存在的语言代码使用默认语言
        result = manager.translate('disk.monitor.status', locale='invalid_locale')
        expected = manager.translate('disk.monitor.status', locale='zh_CN')
        self.assertEqual(result, expected)
        
        # 测试不存在的key返回key本身
        result = manager.translate('non.existent.key', locale='zh_CN')
        self.assertEqual(result, 'non.existent.key')
    
    async def test_parameter_substitution(self):
        """测试参数替换功能"""
        from module.i18n.services.i18n_manager import I18nManager
        
        manager = I18nManager()
        
        # 测试带参数的翻译
        result = manager.translate(
            'language.current',
            locale='zh_CN',
            language='English'
        )
        
        self.assertIn('English', result)
        self.assertIn('当前语言', result)


class TestMongoIntegration(unittest.TestCase):
    """测试MongoDB集成"""
    
    @patch('module.i18n.services.i18n_manager.get_motor_client')
    async def test_mongo_collection_access(self, mock_get_motor):
        """测试MongoDB集合访问"""
        from module.i18n.services.i18n_manager import get_motor_collection
        
        # Mock Motor客户端
        mock_client = AsyncMock()
        mock_get_motor.return_value = mock_client
        mock_db = mock_client['bot']
        mock_collection = mock_db['test_collection']
        
        # 测试集合获取
        collection = await get_motor_collection('test_collection')
        
        # 验证调用
        mock_get_motor.assert_called_once()
        self.assertEqual(collection, mock_collection)


if __name__ == '__main__':
    # 运行异步测试
    async def run_async_tests():
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # 添加测试类
        suite.addTests(loader.loadTestsFromTestCase(TestI18nIntegration))
        suite.addTests(loader.loadTestsFromTestCase(TestMongoIntegration))
        
        runner = unittest.TextTestRunner(verbosity=2)
        
        # 运行所有测试
        for test in suite:
            test_method = getattr(test, test._testMethodName)
            if asyncio.iscoroutinefunction(test_method):
                try:
                    await test_method()
                    print(f"✅ PASS: {test}")
                except Exception as e:
                    print(f"❌ FAIL: {test} - {e}")
            else:
                try:
                    test_method()
                    print(f"✅ PASS: {test}")
                except Exception as e:
                    print(f"❌ FAIL: {test} - {e}")
    
    asyncio.run(run_async_tests())