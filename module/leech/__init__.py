"""
Leech module - File downloading and uploading functionality

This module provides comprehensive file leeching capabilities including:
- Multi-platform file downloading
- Various upload destinations (Telegram, AList, RClone)
- Worker management
- Task monitoring and retry mechanisms
- Setting configuration
"""

__version__ = "1.0.0"
__author__ = "Leech Bot Team"

# Import main components for easy access
from .leech import *

# Import command handlers
from .commands.monitor import *
from .commands.setting import *
from .commands.retry import *
from .commands.terminate import *
from .commands.worker import *

# Core functionality
from .beans.leech_file import LeechFile
from .beans.leech_task import LeechTask
from .constants.task import TaskStatus, TaskType
from .constants.leech_file_status import LeechFileStatus