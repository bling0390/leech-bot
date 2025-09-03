"""
Configuration utilities module - Independent utility functions for configuration
This module is separate from utils.py to avoid circular imports
"""
import os
from typing import Union

from config.config import ALIST_WEB, ALIST_TOKEN, ALIST_HOST


def is_alist_available() -> bool:
    """检查AList是否可用"""
    return all([ALIST_WEB, ALIST_TOKEN]) or all([ALIST_HOST, ALIST_TOKEN])