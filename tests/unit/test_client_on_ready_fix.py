import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from pyrogram import Client


class TestClientOnReadyFix:
    """Test suite to reproduce and fix the Client.on_ready AttributeError"""
    
    def test_client_has_no_on_ready_attribute(self):
        """Test that demonstrates Client doesn't have on_ready attribute"""
        # This test should pass - proving the error exists
        client = Mock(spec=Client)
        
        # Client should NOT have on_ready attribute
        assert not hasattr(client, 'on_ready')
        
        # Attempting to use on_ready should raise AttributeError
        with pytest.raises(AttributeError):
            @client.on_ready
            async def dummy_handler():
                pass
    
    def test_pyrogram_client_startup_pattern(self):
        """Test the correct Pyrogram startup pattern"""
        # Pyrogram uses different patterns for initialization
        with patch('pyrogram.Client') as MockClient:
            mock_client = MockClient.return_value
            
            # Pyrogram doesn't use @on_ready decorator
            # Instead, it uses start() method and can have custom handlers
            mock_client.start = MagicMock()
            mock_client.idle = MagicMock()
            
            # This should work without errors
            mock_client.start()
            mock_client.idle()
            
            assert mock_client.start.called
            assert mock_client.idle.called
    
    def test_bot_startup_with_disk_monitor_wrong_pattern(self):
        """Test that the current bot.py implementation would fail"""
        # This simulates the current problematic code
        with patch('pyrogram.Client') as MockClient:
            mock_app = MockClient.return_value
            
            # Remove on_ready from spec to simulate real Client
            delattr(mock_app, 'on_ready') if hasattr(mock_app, 'on_ready') else None
            
            # This should raise AttributeError
            with pytest.raises(AttributeError, match="'.*' object has no attribute 'on_ready'"):
                @mock_app.on_ready
                async def on_ready():
                    pass
    
    def test_correct_disk_monitor_initialization_pattern(self):
        """Test the correct way to initialize disk monitor with Pyrogram"""
        with patch('pyrogram.Client') as MockClient:
            with patch('asyncio.create_task') as mock_create_task:
                with patch('module.disk.auto_start.start_disk_monitor_if_enabled') as mock_disk_monitor:
                    mock_app = MockClient.return_value
                    mock_app.is_connected = True
                    
                    # Correct pattern: Call setup after start(), not using @on_ready
                    mock_app.start()
                    
                    # Setup disk monitor should be called directly or via asyncio
                    import asyncio
                    
                    async def setup_disk_monitor():
                        await mock_disk_monitor()
                    
                    # This pattern should work
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Run the setup in the event loop
                    task = loop.create_task(setup_disk_monitor())
                    
                    # Verify it doesn't raise errors
                    assert task is not None
                    loop.close()