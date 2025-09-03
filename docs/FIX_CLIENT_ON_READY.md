# Fix: AttributeError - Client object has no attribute 'on_ready'

## Problem
The bot was attempting to use `@app.on_ready` decorator which doesn't exist in Pyrogram. This pattern is from Discord.py, not Pyrogram.

## Root Cause
Pyrogram's `Client` class doesn't have an `on_ready` attribute or decorator. Pyrogram uses different event handlers like `@Client.on_message` for messages.

## Solution
Replace the incorrect `@app.on_ready` decorator with `asyncio.create_task()` after `app.start()`.

### Before (Incorrect)
```python
def startup():
    app = Client(...)
    
    # This doesn't work - Pyrogram doesn't have on_ready
    @app.on_ready
    async def on_ready():
        await setup_disk_monitor()
    
    app.start()
    app.idle()
```

### After (Fixed)
```python
def startup():
    app = Client(...)
    
    app.start()
    
    # Use asyncio.create_task to run the async setup
    asyncio.create_task(setup_disk_monitor())
    
    app.idle()
```

## Key Differences: Pyrogram vs Discord.py

| Discord.py | Pyrogram |
|------------|----------|
| `@client.on_ready` | No equivalent - use `asyncio.create_task()` after `start()` |
| `@client.on_message` | `@Client.on_message` |
| `@client.event` | Various specific decorators |

## Testing
The fix includes comprehensive tests in:
- `tests/unit/test_client_on_ready_fix.py` - Demonstrates the error
- `tests/unit/test_bot_startup_fixed.py` - Tests the fixed implementation
- `tests/unit/test_bot_startup.py` - Updated to reflect new approach

## Prevention
- Always check the documentation for the specific library being used
- Don't assume patterns from one library work in another
- Use TDD to catch such errors early