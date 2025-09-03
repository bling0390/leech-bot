"""
TDD 红灯阶段：验证翻译键映射和语言文件完整性测试

验证语言文件中的翻译键是否完整，以及代码是否正确使用这些键
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestDiskCommandTranslationKeys(unittest.TestCase):
    """TDD 红灯阶段：翻译键映射和语言文件测试"""
    
    def test_language_files_should_have_complete_disk_translations(self):
        """
        失败测试：语言文件应该包含完整的磁盘相关翻译
        """
        import yaml
        from pathlib import Path
        
        # 读取语言文件
        locales_path = Path(__file__).parent.parent.parent / 'locales'
        
        with open(locales_path / 'zh_CN.yml', 'r', encoding='utf-8') as f:
            zh_data = yaml.safe_load(f)
        
        with open(locales_path / 'en_US.yml', 'r', encoding='utf-8') as f:
            en_data = yaml.safe_load(f)
        
        # 检查必需的翻译键是否存在于两种语言中
        required_keys = [
            ('disk', 'status', 'title'),
            ('disk', 'monitor', 'started'),
            ('disk', 'monitor', 'stopped'), 
            ('disk', 'monitor', 'already_running'),
            ('disk', 'monitor', 'not_running'),
            ('disk', 'clean', 'start'),
            ('disk', 'clean', 'complete'),
            ('disk', 'clean', 'failed'),
            ('disk', 'commands', 'help'),
            ('disk', 'buttons', 'status'),
            ('disk', 'buttons', 'start'),
            ('disk', 'buttons', 'stop'),
            ('disk', 'buttons', 'clean')
        ]
        
        missing_zh_keys = []
        missing_en_keys = []
        
        for key_path in required_keys:
            # 检查中文键
            zh_value = zh_data
            en_value = en_data
            
            try:
                for key in key_path:
                    zh_value = zh_value[key]
            except (KeyError, TypeError):
                missing_zh_keys.append('.'.join(key_path))
            
            try:
                for key in key_path:
                    en_value = en_value[key]
            except (KeyError, TypeError):
                missing_en_keys.append('.'.join(key_path))
        
        # 验证：当前语言文件已有这些键（应该通过）
        self.assertEqual(len(missing_zh_keys), 0, 
                        f"zh_CN.yml 缺失翻译键: {missing_zh_keys}")
        self.assertEqual(len(missing_en_keys), 0, 
                        f"en_US.yml 缺失翻译键: {missing_en_keys}")
        
        # 验证：翻译内容不应该相同（中英文应该不同）
        different_translations = 0
        for key_path in required_keys:
            try:
                zh_value = zh_data
                en_value = en_data
                
                for key in key_path:
                    zh_value = zh_value[key]
                    en_value = en_value[key]
                
                if isinstance(zh_value, str) and isinstance(en_value, str):
                    if zh_value != en_value:
                        different_translations += 1
            except:
                pass
        
        self.assertGreater(different_translations, len(required_keys) * 0.8,
                         "中英文翻译应该有明显差异")
    
    def test_disk_command_should_use_correct_translation_keys(self):
        """
        失败测试：磁盘命令应该使用正确的翻译键
        """
        # 这个测试检查代码是否使用了正确的翻译键格式
        import inspect
        import module.disk.commands.disk_monitor as disk_module
        
        source_code = inspect.getsource(disk_module)
        
        # 当前代码中的硬编码中文字符串
        hardcoded_chinese = [
            "磁盘监控启动成功",
            "磁盘状态报告", 
            "正在清理下载目录",
            "磁盘清理完成",
            "磁盘监控已停止"
        ]
        
        found_hardcoded = []
        for text in hardcoded_chinese:
            if text in source_code:
                found_hardcoded.append(text)
        
        # 这个测试会失败，因为当前有很多硬编码中文
        self.assertEqual(len(found_hardcoded), 0,
                        f"代码中不应包含硬编码中文字符串: {found_hardcoded}")
        
        # 检查是否使用了翻译键
        expected_translation_patterns = [
            "disk.monitor.started",
            "disk.status.title", 
            "disk.clean.start",
            "disk.clean.complete",
            "disk.monitor.stopped"
        ]
        
        found_translation_keys = 0
        for pattern in expected_translation_patterns:
            if pattern in source_code:
                found_translation_keys += 1
        
        # 这个测试会失败，因为当前没有使用翻译键
        self.assertGreater(found_translation_keys, 3,
                         f"代码应该使用翻译键，但只找到{found_translation_keys}个")
    
    def test_i18n_integration_should_be_present(self):
        """
        失败测试：应该有i18n集成代码
        """
        import inspect
        import module.disk.commands.disk_monitor as disk_module
        
        source_code = inspect.getsource(disk_module)
        
        # 检查是否有i18n相关的导入和使用
        i18n_patterns = [
            "get_i18n_manager",
            "translate_for_user",
            "from module.i18n",
            "i18n =",
            ".translate("
        ]
        
        found_i18n_patterns = 0
        for pattern in i18n_patterns:
            if pattern in source_code:
                found_i18n_patterns += 1
        
        # 这个测试会失败，因为当前没有i18n集成
        self.assertGreater(found_i18n_patterns, 2,
                         f"应该有i18n集成代码，但只找到{found_i18n_patterns}个相关模式")
    
    def test_user_language_should_be_obtained_in_commands(self):
        """
        失败测试：命令中应该获取用户语言
        """
        import inspect
        import module.disk.commands.disk_monitor as disk_module
        
        # 检查各个命令函数
        command_functions = [
            'handle_disk_status',
            'start_disk_monitor', 
            'stop_disk_monitor',
            'disk_clean',
            'show_disk_help'
        ]
        
        functions_with_user_lang = 0
        
        for func_name in command_functions:
            if hasattr(disk_module, func_name):
                func = getattr(disk_module, func_name)
                source = inspect.getsource(func)
                
                # 检查是否获取用户语言
                user_lang_patterns = [
                    "message.from_user.id",
                    "user_id",
                    "get_user_language",
                    "translate_for_user"
                ]
                
                has_user_lang_logic = any(pattern in source for pattern in user_lang_patterns)
                if has_user_lang_logic:
                    functions_with_user_lang += 1
        
        # 当前所有函数都有 user_id，但没有翻译逻辑
        # 这个测试验证是否有翻译相关的用户语言处理
        translation_functions = 0
        for func_name in command_functions:
            if hasattr(disk_module, func_name):
                func = getattr(disk_module, func_name)
                source = inspect.getsource(func)
                
                if "translate" in source:
                    translation_functions += 1
        
        # 这个测试会失败，因为没有翻译逻辑
        self.assertGreater(translation_functions, 2,
                         f"至少应有3个命令函数包含翻译逻辑，实际只有{translation_functions}个")


if __name__ == '__main__':
    print("=" * 70)
    print("TDD 红灯阶段 - 翻译键映射和语言文件测试")
    print("=" * 70)
    print("验证内容：")
    print("1. 语言文件是否包含完整的磁盘翻译")
    print("2. 代码是否使用正确的翻译键")
    print("3. 是否有i18n集成和用户语言处理")
    print("=" * 70)
    
    unittest.main(verbosity=2)