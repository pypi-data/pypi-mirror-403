"""
Configuration module for adapters and device profiles.
"""

from .manager import ConfigManager
from .adapter import AdapterConfig

__all__ = ["ConfigManager", "AdapterConfig"]