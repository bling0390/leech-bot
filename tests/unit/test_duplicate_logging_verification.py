"""
TDD 绿灯阶段：验证重复日志修复

验证缓存机制有效减少了重复日志输出
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestDuplicateLoggingVerification(unittest.TestCase):
    """TDD 绿灯阶段：验证重复日志修复"""
    
    async def test_cache_prevents_duplicate_get_user_language_calls(self):
        """
        绿灯测试：缓存机制防止重复的 get_user_language 调用
        """
        from module.i18n.services.i18n_manager import get_user_language
        
        user_id = 1076750810
        
        # Mock UserLanguage.get_user_language
        with patch('beans.user_language.UserLanguage.get_user_language', return_value='zh_CN') as mock_get_user_lang:
            # 连续调用4次（模拟 lang_command 的调用场景）
            result1 = await get_user_language(user_id)
            result2 = await get_user_language(user_id)
            result3 = await get_user_language(user_id)
            result4 = await get_user_language(user_id)
            
            # 验证返回结果一致
            self.assertEqual(result1, 'zh_CN')
            self.assertEqual(result2, 'zh_CN')
            self.assertEqual(result3, 'zh_CN')
            self.assertEqual(result4, 'zh_CN')
            
            # 验证：底层方法只被调用1次（其他3次命中缓存）
            self.assertEqual(mock_get_user_lang.call_count, 1, 
                           f"UserLanguage.get_user_language 应该只被调用1次（缓存生效），实际调用了{mock_get_user_lang.call_count}次")
    
    async def test_cache_expires_correctly(self):
        """
        绿灯测试：缓存会正确过期
        """
        from module.i18n.services.i18n_manager import get_user_language, _cache_expire_seconds
        
        # 临时设置较短的缓存时间用于测试
        original_expire = _cache_expire_seconds
        import module.i18n.services.i18n_manager as i18n_module
        i18n_module._cache_expire_seconds = 0.1  # 100毫秒
        
        try:
            user_id = 1076750810
            
            with patch('beans.user_language.UserLanguage.get_user_language', return_value='zh_CN') as mock_get_user_lang:
                # 第一次调用
                result1 = await get_user_language(user_id)
                self.assertEqual(result1, 'zh_CN')
                
                # 等待缓存过期
                time.sleep(0.2)
                
                # 第二次调用（缓存已过期）
                result2 = await get_user_language(user_id)
                self.assertEqual(result2, 'zh_CN')
                
                # 验证：底层方法被调用了2次（缓存过期后重新查询）
                self.assertEqual(mock_get_user_lang.call_count, 2,
                               f"缓存过期后应该重新查询，UserLanguage.get_user_language 应该被调用2次")
        
        finally:
            # 恢复原始缓存时间
            i18n_module._cache_expire_seconds = original_expire
    
    async def test_cache_cleared_when_language_saved(self):
        """
        绿灯测试：保存语言时清除缓存
        """
        from module.i18n.services.i18n_manager import get_user_language, save_user_language_async
        
        user_id = 1076750810
        
        # Mock UserLanguage.get_user_language
        with patch('beans.user_language.UserLanguage.get_user_language', return_value='zh_CN') as mock_get_user_lang:
            # 第一次获取语言（建立缓存）
            result1 = await get_user_language(user_id)
            self.assertEqual(result1, 'zh_CN')
            
            # Mock 保存操作
            with patch('tool.mongo_client.get_motor_client') as mock_client:
                mock_motor_client = AsyncMock()
                mock_db = AsyncMock()
                mock_collection = AsyncMock()
                mock_result = MagicMock()
                mock_result.modified_count = 1
                mock_result.upserted_id = None
                
                mock_client.return_value = mock_motor_client
                mock_motor_client.__getitem__.return_value = mock_db
                mock_db.__getitem__.return_value = mock_collection
                mock_collection.update_one.return_value = mock_result
                
                # 保存新语言（应该清除缓存）
                success = await save_user_language_async(user_id, 'en_US')
                self.assertTrue(success)
            
            # 修改mock返回值
            mock_get_user_lang.return_value = 'en_US'
            
            # 再次获取语言（应该重新查询，因为缓存被清除）
            result2 = await get_user_language(user_id)
            self.assertEqual(result2, 'en_US')
            
            # 验证：底层方法被调用了2次（第一次建立缓存，保存后清除缓存，第二次重新查询）
            self.assertEqual(mock_get_user_lang.call_count, 2,
                           f"保存语言后应该清除缓存并重新查询，UserLanguage.get_user_language 应该被调用2次")
    
    async def test_concurrent_calls_use_same_cache_entry(self):
        """
        绿灯测试：并发调用使用相同的缓存条目
        """
        from module.i18n.services.i18n_manager import get_user_language
        
        user_id = 1076750810
        
        with patch('beans.user_language.UserLanguage.get_user_language', return_value='zh_CN') as mock_get_user_lang:
            # 并发调用多次
            tasks = [get_user_language(user_id) for _ in range(5)]
            results = await asyncio.gather(*tasks)
            
            # 验证所有结果一致
            self.assertTrue(all(result == 'zh_CN' for result in results))
            
            # 验证：底层方法被调用次数合理（理想情况是1次）
            call_count = mock_get_user_lang.call_count
            self.assertLessEqual(call_count, 2, 
                               f"并发调用应该共享缓存，UserLanguage.get_user_language 调用次数应该很少，实际{call_count}次")
    
    async def test_different_users_have_separate_cache(self):
        """
        绿灯测试：不同用户有独立的缓存
        """
        from module.i18n.services.i18n_manager import get_user_language
        
        # Mock 不同用户返回不同语言
        def mock_get_lang_side_effect(user_id):
            if user_id == 123:
                return 'zh_CN'
            elif user_id == 456:
                return 'en_US'
            else:
                return 'zh_CN'
        
        with patch('beans.user_language.UserLanguage.get_user_language', side_effect=mock_get_lang_side_effect) as mock_get_user_lang:
            # 获取不同用户的语言
            result1 = await get_user_language(123)
            result2 = await get_user_language(456)
            result3 = await get_user_language(123)  # 应该命中缓存
            result4 = await get_user_language(456)  # 应该命中缓存
            
            # 验证结果正确
            self.assertEqual(result1, 'zh_CN')
            self.assertEqual(result2, 'en_US')
            self.assertEqual(result3, 'zh_CN')
            self.assertEqual(result4, 'en_US')
            
            # 验证：每个用户的语言只查询一次（2次总调用）
            self.assertEqual(mock_get_user_lang.call_count, 2,
                           f"两个不同用户各查询一次，应该调用2次，实际{mock_get_user_lang.call_count}次")


if __name__ == '__main__':
    print("=" * 70)
    print("TDD 绿灯阶段 - 重复日志修复验证测试")
    print("=" * 70)
    print("验证缓存机制：")
    print("1. 防止重复调用和日志输出")
    print("2. 缓存正确过期")
    print("3. 保存时清除缓存")
    print("4. 并发调用共享缓存")
    print("5. 不同用户独立缓存")
    print("=" * 70)
    
    async def run_verification_tests():
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestDuplicateLoggingVerification)
        
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
        print(f"绿灯阶段结果：通过 {passed}，失败 {failed}")
        if failed == 0:
            print("🎉 所有验证测试通过！重复日志问题已成功修复！")
        else:
            print("⚠️ 部分测试失败，需要进一步优化")
        print("=" * 70)
    
    asyncio.run(run_verification_tests())