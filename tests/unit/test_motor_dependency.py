"""
测试motor依赖是否正确安装和导入

这是TDD流程的红色阶段 - 编写失败测试
"""
import pytest
import sys
import importlib.util


class TestMotorDependency:
    """测试motor模块依赖"""
    
    def test_motor_module_can_be_imported(self):
        """测试motor模块可以被正常导入"""
        try:
            import motor
            import motor.motor_asyncio
            assert True, "motor模块导入成功"
        except ImportError as e:
            pytest.fail(f"motor模块导入失败: {e}")
    
    def test_motor_asyncio_client_available(self):
        """测试AsyncIOMotorClient可以被导入"""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            assert AsyncIOMotorClient is not None
        except ImportError as e:
            pytest.fail(f"AsyncIOMotorClient导入失败: {e}")
    
    def test_motor_asyncio_collection_available(self):
        """测试AsyncIOMotorCollection可以被导入"""
        try:
            from motor.motor_asyncio import AsyncIOMotorCollection
            assert AsyncIOMotorCollection is not None
        except ImportError as e:
            pytest.fail(f"AsyncIOMotorCollection导入失败: {e}")
    
    def test_mongo_client_module_imports_motor(self):
        """测试mongo_client模块可以正常导入motor相关组件"""
        try:
            from tool.mongo_client import get_motor_client, get_collection
            assert get_motor_client is not None
            assert get_collection is not None
        except ImportError as e:
            pytest.fail(f"mongo_client模块导入失败: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])