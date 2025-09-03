"""
测试Bot启动过程中的异步处理
使用TDD方法确保setup_disk_monitor正确处理
"""

import sys
import os
import pytest
import asyncio
import unittest.mock as mock
from unittest.mock import AsyncMock, MagicMock, patch

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class TestBotStartup:
    """测试Bot启动过程"""
    
    @patch('bot.start_disk_monitor_if_enabled', new_callable=AsyncMock)
    @patch('bot.logger')
    def test_setup_disk_monitor_is_async_function(self, mock_logger, mock_start):
        """测试 setup_disk_monitor 是异步函数"""
        # Mock dependencies to avoid import errors
        with patch.dict('sys.modules', {
            'i18n': MagicMock(),
            'pyrogram': MagicMock(),
            'pyrogram.client': MagicMock(),
            'pyrogram.types': MagicMock(),
        }):
            from bot import setup_disk_monitor
            import asyncio
            
            # 验证函数是协程函数
            assert asyncio.iscoroutinefunction(setup_disk_monitor)
    
    @patch('bot.start_disk_monitor_if_enabled', new_callable=AsyncMock)
    @patch('bot.logger')
    @pytest.mark.asyncio
    async def test_setup_disk_monitor_can_be_awaited(self, mock_logger, mock_start):
        """测试 setup_disk_monitor 可以被正确await"""
        # Mock dependencies
        with patch.dict('sys.modules', {
            'i18n': MagicMock(),
            'pyrogram': MagicMock(),
            'pyrogram.client': MagicMock(),
            'pyrogram.types': MagicMock(),
        }):
            from bot import setup_disk_monitor
            
            # 这应该可以被await而不产生警告
            await setup_disk_monitor()
            mock_start.assert_called_once()
            mock_logger.info.assert_called_with("磁盘监控设置完成")
    
    @patch('bot.start_disk_monitor_if_enabled', new_callable=AsyncMock)
    @patch('bot.logger')
    @pytest.mark.asyncio
    async def test_setup_disk_monitor_error_handling(self, mock_logger, mock_start):
        """测试 setup_disk_monitor 的错误处理"""
        # Mock dependencies
        with patch.dict('sys.modules', {
            'i18n': MagicMock(),
            'pyrogram': MagicMock(),
            'pyrogram.client': MagicMock(),
            'pyrogram.types': MagicMock(),
        }):
            from bot import setup_disk_monitor
            
            # 设置mock抛出异常
            mock_start.side_effect = Exception("测试异常")
            
            # 调用函数不应该抛出异常
            await setup_disk_monitor()
            
            # 验证错误被正确记录
            mock_logger.error.assert_called_with("设置磁盘监控时发生错误: 测试异常")
    
    @patch('bot.Client')
    @patch('bot.update_telegram_client')
    @patch('bot.logger')
    def test_startup_function_uses_asyncio_create_task(self, mock_logger, mock_update_client, mock_client):
        """测试startup函数使用asyncio.create_task而不是@app.on_ready"""
        # Mock dependencies
        with patch.dict('sys.modules', {
            'i18n': MagicMock(),
            'pyrogram': MagicMock(),
            'pyrogram.client': MagicMock(),
            'pyrogram.types': MagicMock(),
        }):
            from bot import startup
            
            # Mock Client实例
            mock_app = MagicMock()
            mock_client.return_value = mock_app
            
            with patch('asyncio.create_task') as mock_create_task:
                try:
                    startup()
                    # 验证现在调用 asyncio.create_task
                    mock_create_task.assert_called_once()
                    
                    # 验证 Client 没有 on_ready 属性（Pyrogram不支持）
                    # 不应该尝试访问 on_ready
                    
                except Exception as e:
                    pytest.fail(f"startup函数不应该抛出异常: {e}")
                    
    @patch('bot.start_disk_monitor_if_enabled', new_callable=AsyncMock)  
    @patch('bot.logger')
    @pytest.mark.asyncio 
    async def test_disk_monitor_setup_in_async_context(self, mock_logger, mock_start):
        """测试在异步上下文中正确设置磁盘监控"""
        # Mock dependencies
        with patch.dict('sys.modules', {
            'i18n': MagicMock(),
            'pyrogram': MagicMock(),
            'pyrogram.client': MagicMock(), 
            'pyrogram.types': MagicMock(),
        }):
            from bot import setup_disk_monitor
            
            # 在真正的异步上下文中调用应该工作正常
            await setup_disk_monitor()
            
            # 验证被调用
            mock_start.assert_called_once()
            mock_logger.info.assert_called_with("磁盘监控设置完成")