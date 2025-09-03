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

# 避免循环导入，移除 star imports
# 只导入核心数据类，不导入依赖tool.utils的命令模块

# Core functionality - 只导入数据类和常量
from .beans.leech_file import LeechFile
from .beans.leech_task import LeechTask
from .constants.task import TaskStatus, TaskType
from .constants.leech_file_status import LeechFileStatus

# 注意：命令模块(commands/*)将按需导入，避免循环依赖