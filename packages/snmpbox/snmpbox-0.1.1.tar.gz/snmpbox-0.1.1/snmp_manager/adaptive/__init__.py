"""
Adaptive module for dynamic adapter generation and self-learning capabilities.
"""

from .adapter_generator import AdapterGenerator
from .self_learning import SelfLearningEngine
from .fallback_strategies import FallbackStrategies

__all__ = ["AdapterGenerator", "SelfLearningEngine", "FallbackStrategies"]