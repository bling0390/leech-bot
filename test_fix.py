#!/usr/bin/env python3
"""
Quick test to verify the Client.on_ready fix works
"""

import sys
import asyncio
from unittest.mock import Mock, patch, AsyncMock

def test_pyrogram_client_no_on_ready():
    """Test that Pyrogram Client doesn't have on_ready"""
    try:
        from pyrogram import Client
        
        # Create a mock client
        client = Client("test_session")
        
        # This should fail if on_ready exists
        assert not hasattr(client, 'on_ready'), "Client should not have on_ready attribute"
        print("✅ Test 1 passed: Client doesn't have on_ready attribute")
        
    except ImportError:
        print("⚠️  Pyrogram not installed, skipping test")
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")

def test_asyncio_create_task_pattern():
    """Test that asyncio.create_task pattern works"""
    try:
        async def mock_setup():
            """Mock setup function"""
            return "Setup complete"
        
        async def main():
            # This is the pattern we use in the fix
            task = asyncio.create_task(mock_setup())
            # Wait a bit to let task start
            await asyncio.sleep(0.1)
            return task
        
        # Run the test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        task = loop.run_until_complete(main())
        
        assert task is not None, "Task should be created"
        print("✅ Test 2 passed: asyncio.create_task pattern works")
        
        loop.close()
        
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")

def test_bot_py_syntax():
    """Test that bot.py has correct syntax"""
    try:
        with open('bot.py', 'r') as f:
            content = f.read()
        
        # Check the fix is in place
        assert '@app.on_ready' not in content, "Old pattern should be removed"
        assert 'asyncio.create_task(setup_disk_monitor())' in content, "New pattern should be present"
        
        # Try to compile the file to check syntax
        compile(content, 'bot.py', 'exec')
        
        print("✅ Test 3 passed: bot.py has correct syntax and fix is in place")
        
    except SyntaxError as e:
        print(f"❌ Test 3 failed - Syntax error in bot.py: {e}")
    except AssertionError as e:
        print(f"❌ Test 3 failed - Fix not properly applied: {e}")
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")

if __name__ == "__main__":
    print("Testing Client.on_ready fix...")
    print("-" * 40)
    
    test_pyrogram_client_no_on_ready()
    test_asyncio_create_task_pattern()
    test_bot_py_syntax()
    
    print("-" * 40)
    print("Testing complete!")