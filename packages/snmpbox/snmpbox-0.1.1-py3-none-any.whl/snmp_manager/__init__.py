"""
SNMP Manager - Intelligent SNMP Data Collection System

A robust system for collecting data from multivendor telecom devices
with automatic discovery, reverse engineering, and uniform output.
"""

__version__ = "0.1.1"
__author__ = "Yusef Ulum"
__email__ = "yusef314159@gmail.com"
__copyright__ = "Copyright (c) 2025 Yusef Ulum"
__license__ = "MIT"
__url__ = "https://github.com/mexyusef/snmp-manager"

# Core imports
from .core.manager import SNMPManager
from .core.device import Device
from .core.engine import SNMPEngine
from .core.enhanced_device import EnhancedDevice

# Discovery imports
from .discovery.scanner import NetworkScanner
from .discovery.fingerprinter import DeviceFingerprinter

# Intelligence imports
from .intelligence.oid_explorer import OIDExplorer
from .intelligence.reverse_engineer import ReverseEngineer
from .intelligence.knowledge_base import KnowledgeBase
from .intelligence.pattern_recognition import PatternMatcher

# Adaptive imports
from .adaptive.adapter_generator import AdapterGenerator
from .adaptive.self_learning import SelfLearningEngine
from .adaptive.fallback_strategies import FallbackStrategies

__all__ = [
    # Core classes
    "SNMPManager",
    "Device",
    "EnhancedDevice",
    "SNMPEngine",

    # Discovery classes
    "NetworkScanner",
    "DeviceFingerprinter",

    # Intelligence classes
    "OIDExplorer",
    "ReverseEngineer",
    "KnowledgeBase",
    "PatternMatcher",

    # Adaptive classes
    "AdapterGenerator",
    "SelfLearningEngine",
    "FallbackStrategies",
]