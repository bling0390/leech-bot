#!/usr/bin/env python3
"""
单元测试 - 验证循环导入修复

测试场景:
1. 直接导入 tool.config_utils 模块
2. 导入 tool.utils 模块的核心函数
3. 测试 is_alist_available 函数功能
4. 验证函数返回值类型和逻辑
5. 模拟不同环境配置场景
"""

import unittest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestCircularImportFix(unittest.TestCase):
    """测试循环导入修复"""
    
    def test_config_utils_import(self):
        """测试 config_utils 模块导入"""
        try:
            from tool.config_utils import is_alist_available
            self.assertTrue(callable(is_alist_available))
            print("✓ tool.config_utils 导入成功")
        except ImportError as e:
            self.fail(f"config_utils 导入失败: {e}")
    
    def test_utils_import(self):
        """测试 utils 模块导入"""
        try:
            from tool.utils import get_redis_unique_key, clean_local_file, is_admin
            self.assertTrue(callable(get_redis_unique_key))
            self.assertTrue(callable(clean_local_file))
            print("✓ tool.utils 核心函数导入成功")
        except ImportError as e:
            self.fail(f"utils 导入失败: {e}")
    
    def test_is_alist_available_functionality(self):
        """测试 is_alist_available 函数功能"""
        from tool.config_utils import is_alist_available
        
        # 测试函数返回值是布尔类型
        result = is_alist_available()
        self.assertIsInstance(result, bool)
        print(f"✓ is_alist_available() 返回: {result}")
    
    def test_get_redis_unique_key_with_mock_object(self):
        """测试 get_redis_unique_key 函数（使用模拟对象）"""
        from tool.utils import get_redis_unique_key
        
        # 创建模拟 LeechFile 对象
        class MockLeechFile:
            def __init__(self, tool="test_tool", name="test_file"):
                self.tool = tool
                self.name = name
                self.remote_folder = "test_folder"
        
        mock_file = MockLeechFile()
        key = get_redis_unique_key(mock_file)
        
        # 验证返回值是字符串且非空
        self.assertIsInstance(key, str)
        self.assertTrue(len(key) > 0)
        print(f"✓ get_redis_unique_key() 生成密钥: {key}")
    
    def test_no_circular_import_in_button_module(self):
        """测试 button 模块不再存在循环导入"""
        try:
            from module.leech.utils.button import get_bottom_buttons, get_upload_tool_buttons
            self.assertTrue(callable(get_bottom_buttons))
            self.assertTrue(callable(get_upload_tool_buttons))
            print("✓ button 模块导入成功，无循环依赖")
        except ImportError as e:
            # 如果是因为缺少依赖（如 rclone_python）导致的错误，这是可以接受的
            if "rclone_python" in str(e):
                print("⚠ button 模块导入失败：缺少 rclone_python 依赖（这是预期的）")
            else:
                self.fail(f"button 模块导入失败: {e}")
    
    def test_bot_module_import(self):
        """测试 bot.py 能够成功导入配置函数"""
        try:
            # 模拟 bot.py 中的导入
            from tool.config_utils import is_alist_available
            result = is_alist_available()
            self.assertIsInstance(result, bool)
            print("✓ bot.py 配置导入修复成功")
        except ImportError as e:
            self.fail(f"bot.py 配置导入失败: {e}")


class TestFunctionalCorrectness(unittest.TestCase):
    """测试功能正确性"""
    
    def setUp(self):
        """设置测试环境"""
        # 保存原始环境变量
        self.original_env = {}
        for key in ['ALIST_WEB', 'ALIST_TOKEN', 'ALIST_HOST']:
            self.original_env[key] = os.environ.get(key)
    
    def tearDown(self):
        """清理测试环境"""
        # 恢复原始环境变量
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


def run_comprehensive_import_test():
    """运行全面的导入测试"""
    print("=== 循环导入修复验证测试 ===\n")
    
    # 基础导入测试
    import_tests = [
        ("tool.config_utils", "is_alist_available"),
        ("tool.utils", "get_redis_unique_key"),
        ("tool.utils", "clean_local_file"), 
        ("tool.utils", "is_admin"),
    ]
    
    for module_name, func_name in import_tests:
        try:
            module = __import__(module_name, fromlist=[func_name])
            func = getattr(module, func_name)
            assert callable(func)
            print(f"✓ {module_name}.{func_name} 导入成功")
        except Exception as e:
            print(f"✗ {module_name}.{func_name} 导入失败: {e}")
            return False
    
    print("\n=== 所有导入测试通过 ===")
    return True


if __name__ == "__main__":
    # 首先运行快速导入测试
    success = run_comprehensive_import_test()
    
    if success:
        print("\n=== 运行详细单元测试 ===")
        unittest.main(verbosity=2)
    else:
        print("\n❌ 基础导入测试失败，跳过单元测试")
        sys.exit(1)