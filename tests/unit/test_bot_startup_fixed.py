import pytest
import asyncio
import sys
from unittest.mock import Mock, patch, MagicMock, AsyncMock, call
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestBotStartupFixed:
    """Test suite for the fixed bot startup implementation"""
    
    @patch('bot.EstablishMongodbConnection')
    @patch('bot.setup_rclone')
    @patch('bot.setup_locale')
    @patch('bot.setup_logger')
    @patch('bot.setup_timezone')
    @patch('bot.check_environment_variables')
    @patch('bot.update_telegram_client')
    @patch('bot.Client')
    @patch('bot.asyncio.create_task')
    @patch('bot.setup_disk_monitor', new_callable=AsyncMock)
    def test_startup_with_fixed_disk_monitor(
        self,
        mock_setup_disk_monitor,
        mock_create_task,
        MockClient,
        mock_update_telegram_client,
        mock_check_env,
        mock_setup_tz,
        mock_setup_logger,
        mock_setup_locale,
        mock_setup_rclone,
        mock_setup_mongo
    ):
        """Test that the fixed startup correctly initializes disk monitor"""
        # Setup
        mock_app = MockClient.return_value
        mock_app.start = MagicMock()
        mock_app.idle = MagicMock()
        mock_app.set_parse_mode = MagicMock()
        
        # Import and run startup
        from bot import startup
        
        # Execute
        startup()
        
        # Verify correct order of operations
        MockClient.assert_called_once()
        mock_update_telegram_client.assert_called_once_with(mock_app)
        from pyrogram.enums import ParseMode
        mock_app.set_parse_mode.assert_called_once_with(ParseMode.HTML)
        mock_app.start.assert_called_once()
        
        # Verify disk monitor is set up using asyncio.create_task
        mock_create_task.assert_called_once()
        
        # The argument to create_task should be the coroutine
        task_arg = mock_create_task.call_args[0][0]
        assert asyncio.iscoroutine(task_arg)
        
        mock_app.idle.assert_called_once()
    
    @patch('bot.start_disk_monitor_if_enabled', new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_setup_disk_monitor_function(self, mock_start_disk_monitor):
        """Test the setup_disk_monitor function works correctly"""
        from bot import setup_disk_monitor
        
        # Execute
        await setup_disk_monitor()
        
        # Verify
        mock_start_disk_monitor.assert_called_once()
    
    @patch('bot.start_disk_monitor_if_enabled', new_callable=AsyncMock)
    @patch('bot.logger')
    @pytest.mark.asyncio
    async def test_setup_disk_monitor_handles_errors(self, mock_logger, mock_start_disk_monitor):
        """Test that setup_disk_monitor handles errors gracefully"""
        from bot import setup_disk_monitor
        
        # Setup - make the disk monitor raise an exception
        mock_start_disk_monitor.side_effect = Exception("Test error")
        
        # Execute
        await setup_disk_monitor()
        
        # Verify error is logged
        mock_logger.error.assert_called_once()
        error_message = mock_logger.error.call_args[0][0]
        assert "Test error" in error_message
    
    def test_no_on_ready_decorator_used(self):
        """Test that the fixed code doesn't use @app.on_ready"""
        # Read the bot.py file
        with open('/root/ideas/Alist-bot/bot.py', 'r') as f:
            content = f.read()
        
        # Verify @app.on_ready is not in the file
        assert '@app.on_ready' not in content
        
        # Verify asyncio.create_task is used instead
        assert 'asyncio.create_task(setup_disk_monitor())' in content
    
    @patch('bot.Client')
    def test_pyrogram_client_doesnt_have_on_ready(self, MockClient):
        """Verify that Pyrogram Client doesn't have on_ready attribute"""
        from pyrogram import Client
        
        # Real Client shouldn't have on_ready
        client = Client('test')
        assert not hasattr(client, 'on_ready')
    
    @patch('bot.EstablishMongodbConnection')
    @patch('bot.setup_rclone')
    @patch('bot.setup_locale')
    @patch('bot.setup_logger')
    @patch('bot.setup_timezone')
    @patch('bot.check_environment_variables')
    def test_main_execution_order(
        self,
        mock_check_env,
        mock_setup_tz,
        mock_setup_logger,
        mock_setup_locale,
        mock_setup_rclone,
        mock_setup_mongo
    ):
        """Test that main execution follows correct order"""
        with patch('bot.startup') as mock_startup:
            # Import the module to trigger __main__ execution
            import bot
            
            if bot.__name__ == '__main__':
                bot.check_environment_variables()
                bot.setup_timezone()
                bot.setup_logger()
                bot.setup_locale()
                bot.setup_rclone()
                bot.setup_mongo()
                bot.startup()
            
            # Verify order
            mock_check_env.assert_called_once()
            mock_setup_tz.assert_called_once()
            mock_setup_logger.assert_called_once()
            mock_setup_locale.assert_called_once()
            mock_setup_rclone.assert_called_once()
            mock_setup_mongo.assert_called_once()
            mock_startup.assert_called_once()