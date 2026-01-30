"""
Fallback Strategies - Multiple collection methods with graceful degradation.

This module implements various fallback strategies for collecting data
from devices when primary methods fail.
"""

import asyncio
import logging
from typing import Dict, List, Set, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import time
from collections import defaultdict

from ..core.engine import SNMPEngine, SNMPTarget, SNMPResponse, SNMPVersion
from ..intelligence.oid_explorer import OIDExplorer, OIDNode

logger = logging.getLogger(__name__)


class CollectionMethod(Enum):
    """Collection method types."""
    GET_BULK = "get_bulk"
    GET_NEXT = "get_next"
    GET = "get"
    WALK = "walk"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    ADAPTIVE = "adaptive"


@dataclass
class StrategyResult:
    """Result of a collection strategy attempt."""
    method: CollectionMethod
    success: bool
    collected_oids: List[str]
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    data_quality_score: float = 0.0


@dataclass
class FallbackStrategy:
    """Fallback strategy configuration."""
    name: str
    priority: int
    methods: List[CollectionMethod]
    timeout_multiplier: float = 1.0
    retry_multiplier: int = 1
    oid_batch_size: int = 20
    concurrent_requests: int = 10
    adaptive_parameters: Dict[str, Any] = field(default_factory=dict)


class FallbackStrategies:
    """
    Collection fallback strategies with graceful degradation.

    Features:
    - Multiple collection methods with automatic fallback
    - Adaptive timeout and retry logic
    - Method-specific optimization
    - Performance monitoring and learning
    - Error recovery and retry strategies
    """

    def __init__(self, snmp_engine: SNMPEngine = None):
        """
        Initialize fallback strategies.

        Args:
            snmp_engine: SNMP engine to use for operations
        """
        self.snmp_engine = snmp_engine or SNMPEngine()
        self.oid_explorer = OIDExplorer(self.snmp_engine)

        # Strategy definitions
        self.strategies: Dict[str, FallbackStrategy] = {}
        self._load_builtin_strategies()

        # Performance tracking
        self.method_performance: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            "success_rate": 0.0,
            "avg_response_time": 0.0,
            "avg_data_quality": 0.0,
            "usage_count": 0
        })

        # Device-specific preferences
        self.device_preferences: Dict[str, Dict[str, Any]] = {}

    def _load_builtin_strategies(self):
        """Load built-in fallback strategies."""
        # Standard strategy - works for most devices
        self.strategies["standard"] = FallbackStrategy(
            name="standard",
            priority=1,
            methods=[
                CollectionMethod.GET_BULK,
                CollectionMethod.WALK,
                CollectionMethod.GET_NEXT,
                CollectionMethod.GET
            ],
            timeout_multiplier=1.0,
            retry_multiplier=1,
            oid_batch_size=20,
            concurrent_requests=10
        )

        # Conservative strategy - for problematic devices
        self.strategies["conservative"] = FallbackStrategy(
            name="conservative",
            priority=2,
            methods=[
                CollectionMethod.GET,
                CollectionMethod.GET_NEXT,
                CollectionMethod.WALK
            ],
            timeout_multiplier=2.0,
            retry_multiplier=2,
            oid_batch_size=5,
            concurrent_requests=3
        )

        # Aggressive strategy - for high-performance devices
        self.strategies["aggressive"] = FallbackStrategy(
            name="aggressive",
            priority=3,
            methods=[
                CollectionMethod.PARALLEL,
                CollectionMethod.GET_BULK,
                CollectionMethod.WALK
            ],
            timeout_multiplier=0.5,
            retry_multiplier=1,
            oid_batch_size=50,
            concurrent_requests=20
        )

        # Adaptive strategy - learns from device behavior
        self.strategies["adaptive"] = FallbackStrategy(
            name="adaptive",
            priority=4,
            methods=[
                CollectionMethod.ADAPTIVE,
                CollectionMethod.GET_BULK,
                CollectionMethod.GET_NEXT
            ],
            timeout_multiplier=1.5,
            retry_multiplier=1,
            oid_batch_size=15,
            concurrent_requests=8,
            adaptive_parameters={
                "learning_enabled": True,
                "performance_threshold": 0.7,
                "method_switching": True
            }
        )

        # V-SOL specific strategy - for undocumented V-SOL devices
        self.strategies["vsol"] = FallbackStrategy(
            name="vsol",
            priority=5,
            methods=[
                CollectionMethod.GET,
                CollectionMethod.GET_NEXT,
                CollectionMethod.WALK
            ],
            timeout_multiplier=3.0,
            retry_multiplier=3,
            oid_batch_size=3,
            concurrent_requests=2
        )

    async def collect_with_fallback(
        self,
        target: SNMPTarget,
        oids: List[str],
        strategy_name: str = "standard",
        device_signature: Dict[str, Any] = None
    ) -> Tuple[Dict[str, Any], List[StrategyResult]]:
        """
        Collect data using fallback strategies.

        Args:
            target: SNMP target
            oids: List of OIDs to collect
            strategy_name: Strategy to use
            device_signature: Device signature for adaptive behavior

        Returns:
            Tuple of (collected_data, strategy_results)
        """
        logger.info(f"Collecting {len(oids)} OIDs from {target.host} using strategy: {strategy_name}")

        strategy = self.strategies.get(strategy_name, self.strategies["standard"])
        collected_data = {}
        strategy_results = []

        # Apply device-specific adjustments
        adjusted_strategy = self._adjust_strategy_for_device(strategy, target, device_signature)

        # Try each method in the strategy
        for method in adjusted_strategy.methods:
            start_time = time.time()
            try:
                result = await self._execute_method(
                    method, target, oids, adjusted_strategy
                )

                # Record method performance
                self._record_method_performance(method, result, target.host)

                if result.success and result.collected_oids:
                    # Merge collected data
                    method_data = await self._extract_method_data(result, target)
                    collected_data.update(method_data)

                    strategy_results.append(result)
                    logger.debug(f"Method {method.value} succeeded: {len(result.collected_oids)} OIDs")

                    # If we got good results, we can stop for most strategies
                    if len(collected_data) >= len(oids) * 0.8:  # 80% threshold
                        break
                else:
                    strategy_results.append(result)
                    logger.debug(f"Method {method.value} failed: {result.error_message}")

            except Exception as e:
                error_result = StrategyResult(
                    method=method,
                    success=False,
                    collected_oids=[],
                    error_message=str(e),
                    execution_time_ms=(time.time() - start_time) * 1000
                )
                strategy_results.append(error_result)
                logger.error(f"Method {method.value} threw exception: {e}")

        # Update device preferences based on results
        self._update_device_preferences(target.host, strategy_results)

        logger.info(f"Collection completed: {len(collected_data)}/{len(oids)} OIDs collected")
        return collected_data, strategy_results

    async def _execute_method(
        self,
        method: CollectionMethod,
        target: SNMPTarget,
        oids: List[str],
        strategy: FallbackStrategy
    ) -> StrategyResult:
        """Execute a specific collection method."""
        start_time = time.time()

        if method == CollectionMethod.GET_BULK:
            return await self._execute_get_bulk(target, oids, strategy)
        elif method == CollectionMethod.GET_NEXT:
            return await self._execute_get_next(target, oids, strategy)
        elif method == CollectionMethod.GET:
            return await self._execute_get(target, oids, strategy)
        elif method == CollectionMethod.WALK:
            return await self._execute_walk(target, oids, strategy)
        elif method == CollectionMethod.PARALLEL:
            return await self._execute_parallel(target, oids, strategy)
        elif method == CollectionMethod.SEQUENTIAL:
            return await self._execute_sequential(target, oids, strategy)
        elif method == CollectionMethod.ADAPTIVE:
            return await self._execute_adaptive(target, oids, strategy)
        else:
            raise ValueError(f"Unknown collection method: {method}")

    async def _execute_get_bulk(
        self,
        target: SNMPTarget,
        oids: List[str],
        strategy: FallbackStrategy
    ) -> StrategyResult:
        """Execute GET_BULK collection method."""
        collected_oids = []
        errors = []

        # Process OIDs in batches
        batch_size = strategy.oid_batch_size
        for i in range(0, len(oids), batch_size):
            batch = oids[i:i + batch_size]

            try:
                response = await self.snmp_engine.bulk_cmd(
                    target,
                    batch,
                    max_repetitions=20,
                    timeout=int(target.timeout * strategy.timeout_multiplier)
                )

                if response.success and response.var_binds:
                    for oid_str, value in response.var_binds:
                        collected_oids.append(oid_str)
                else:
                    errors.append(f"Bulk operation failed: {response.error_indication}")

            except Exception as e:
                errors.append(f"Bulk batch {i//batch_size} failed: {e}")

        return StrategyResult(
            method=CollectionMethod.GET_BULK,
            success=len(collected_oids) > 0,
            collected_oids=collected_oids,
            error_message="; ".join(errors) if errors else None,
            execution_time_ms=0.0,  # Will be set by caller
            data_quality_score=self._calculate_data_quality(collected_oids, oids)
        )

    async def _execute_get_next(
        self,
        target: SNMPTarget,
        oids: List[str],
        strategy: FallbackStrategy
    ) -> StrategyResult:
        """Execute GET_NEXT collection method."""
        collected_oids = []
        errors = []

        for oid in oids:
            try:
                response = await self.snmp_engine.next_cmd(
                    target,
                    [oid],
                    timeout=int(target.timeout * strategy.timeout_multiplier)
                )

                if response.success and response.var_binds:
                    for oid_str, value in response.var_binds:
                        collected_oids.append(oid_str)
                else:
                    errors.append(f"GET_NEXT failed for {oid}: {response.error_indication}")

            except Exception as e:
                errors.append(f"GET_NEXT exception for {oid}: {e}")

        return StrategyResult(
            method=CollectionMethod.GET_NEXT,
            success=len(collected_oids) > 0,
            collected_oids=collected_oids,
            error_message="; ".join(errors) if errors else None,
            data_quality_score=self._calculate_data_quality(collected_oids, oids)
        )

    async def _execute_get(
        self,
        target: SNMPTarget,
        oids: List[str],
        strategy: FallbackStrategy
    ) -> StrategyResult:
        """Execute GET collection method."""
        collected_oids = []
        errors = []

        for oid in oids:
            try:
                response = await self.snmp_engine.get_cmd(
                    target,
                    [oid],
                    timeout=int(target.timeout * strategy.timeout_multiplier)
                )

                if response.success and response.var_binds:
                    for oid_str, value in response.var_binds:
                        collected_oids.append(oid_str)
                else:
                    errors.append(f"GET failed for {oid}: {response.error_indication}")

            except Exception as e:
                errors.append(f"GET exception for {oid}: {e}")

        return StrategyResult(
            method=CollectionMethod.GET,
            success=len(collected_oids) > 0,
            collected_oids=collected_oids,
            error_message="; ".join(errors) if errors else None,
            data_quality_score=self._calculate_data_quality(collected_oids, oids)
        )

    async def _execute_walk(
        self,
        target: SNMPTarget,
        oids: List[str],
        strategy: FallbackStrategy
    ) -> StrategyResult:
        """Execute WALK collection method."""
        collected_oids = []
        errors = []

        for oid in oids:
            try:
                response = await self.snmp_engine.walk_cmd(
                    target,
                    oid,
                    timeout=int(target.timeout * strategy.timeout_multiplier)
                )

                if response.success and response.var_binds:
                    for oid_str, value in response.var_binds:
                        collected_oids.append(oid_str)
                else:
                    errors.append(f"WALK failed for {oid}: {response.error_indication}")

            except Exception as e:
                errors.append(f"WALK exception for {oid}: {e}")

        return StrategyResult(
            method=CollectionMethod.WALK,
            success=len(collected_oids) > 0,
            collected_oids=collected_oids,
            error_message="; ".join(errors) if errors else None,
            data_quality_score=self._calculate_data_quality(collected_oids, oids)
        )

    async def _execute_parallel(
        self,
        target: SNMPTarget,
        oids: List[str],
        strategy: FallbackStrategy
    ) -> StrategyResult:
        """Execute parallel collection method."""
        # Create batches for parallel processing
        batch_size = max(1, len(oids) // strategy.concurrent_requests)
        batches = [oids[i:i + batch_size] for i in range(0, len(oids), batch_size)]

        tasks = []
        for batch in batches:
            task = self._execute_get(target, batch, strategy)
            tasks.append(task)

        # Execute batches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        collected_oids = []
        errors = []

        for i, result in enumerate(results):
            if isinstance(result, StrategyResult):
                if result.success:
                    collected_oids.extend(result.collected_oids)
                if result.error_message:
                    errors.append(f"Batch {i}: {result.error_message}")
            else:
                errors.append(f"Batch {i} exception: {result}")

        return StrategyResult(
            method=CollectionMethod.PARALLEL,
            success=len(collected_oids) > 0,
            collected_oids=collected_oids,
            error_message="; ".join(errors) if errors else None,
            data_quality_score=self._calculate_data_quality(collected_oids, oids)
        )

    async def _execute_sequential(
        self,
        target: SNMPTarget,
        oids: List[str],
        strategy: FallbackStrategy
    ) -> StrategyResult:
        """Execute sequential collection method."""
        collected_oids = []
        errors = []

        # Try methods in sequence: GET -> GET_NEXT -> WALK
        methods = [CollectionMethod.GET, CollectionMethod.GET_NEXT, CollectionMethod.WALK]

        for method in methods:
            try:
                result = await self._execute_method(method, target, oids, strategy)

                if result.success:
                    collected_oids.extend(result.collected_oids)
                    # Stop if we got good results
                    if len(collected_oids) >= len(oids) * 0.5:
                        break

                if result.error_message:
                    errors.append(f"{method.value}: {result.error_message}")

            except Exception as e:
                errors.append(f"{method.value} exception: {e}")

        return StrategyResult(
            method=CollectionMethod.SEQUENTIAL,
            success=len(collected_oids) > 0,
            collected_oids=collected_oids,
            error_message="; ".join(errors) if errors else None,
            data_quality_score=self._calculate_data_quality(collected_oids, oids)
        )

    async def _execute_adaptive(
        self,
        target: SNMPTarget,
        oids: List[str],
        strategy: FallbackStrategy
    ) -> StrategyResult:
        """Execute adaptive collection method."""
        # Get device preferences
        device_key = f"{target.host}:{target.port}"
        preferences = self.device_preferences.get(device_key, {})

        # Start with preferred method
        preferred_method = preferences.get("preferred_method", CollectionMethod.GET_BULK)

        # Check if we have performance data
        method_perf = self.method_performance.get(preferred_method.value, {})
        if method_perf["success_rate"] < 0.5:
            # Try alternative method
            preferred_method = CollectionMethod.GET

        # Execute preferred method first
        result = await self._execute_method(preferred_method, target, oids, strategy)

        # If not successful, try fallback
        if not result.success or len(result.collected_oids) < len(oids) * 0.3:
            fallback_methods = [m for m in [CollectionMethod.GET, CollectionMethod.GET_NEXT]
                              if m != preferred_method]

            for fallback_method in fallback_methods:
                fallback_result = await self._execute_method(fallback_method, target, oids, strategy)
                if fallback_result.success:
                    result.collected_oids.extend(fallback_result.collected_oids)
                    break

        result.success = len(result.collected_oids) > 0
        result.data_quality_score = self._calculate_data_quality(result.collected_oids, oids)

        return result

    def _adjust_strategy_for_device(
        self,
        strategy: FallbackStrategy,
        target: SNMPTarget,
        device_signature: Dict[str, Any] = None
    ) -> FallbackStrategy:
        """Adjust strategy parameters based on device characteristics."""
        adjusted = FallbackStrategy(
            name=strategy.name,
            priority=strategy.priority,
            methods=strategy.methods.copy(),
            timeout_multiplier=strategy.timeout_multiplier,
            retry_multiplier=strategy.retry_multiplier,
            oid_batch_size=strategy.oid_batch_size,
            concurrent_requests=strategy.concurrent_requests,
            adaptive_parameters=strategy.adaptive_parameters.copy()
        )

        # Adjust for known problematic vendors
        if device_signature:
            vendor = device_signature.get("vendor", "").lower()
            if vendor == "vsol":
                adjusted.timeout_multiplier *= 2.0
                adjusted.retry_multiplier *= 2
                adjusted.concurrent_requests = max(2, adjusted.concurrent_requests // 2)
            elif vendor == "huawei":
                # Huawei devices usually handle bulk operations well
                adjusted.oid_batch_size = min(50, adjusted.oid_batch_size * 2)
                adjusted.concurrent_requests = min(25, adjusted.concurrent_requests * 2)
            elif vendor == "zte":
                # ZTE devices - moderate adjustments
                adjusted.timeout_multiplier *= 1.5

        # Apply device-specific preferences
        device_key = f"{target.host}:{target.port}"
        if device_key in self.device_preferences:
            prefs = self.device_preferences[device_key]
            if "timeout_multiplier" in prefs:
                adjusted.timeout_multiplier = prefs["timeout_multiplier"]
            if "concurrent_requests" in prefs:
                adjusted.concurrent_requests = prefs["concurrent_requests"]

        return adjusted

    def _calculate_data_quality(self, collected_oids: List[str], requested_oids: List[str]) -> float:
        """Calculate data quality score."""
        if not requested_oids:
            return 0.0

        # Coverage (how many requested OIDs were collected)
        coverage = len(collected_oids) / len(requested_oids)

        # Completeness (are we getting full OID branches?)
        completeness = 1.0 if coverage > 0.8 else 0.5 if coverage > 0.5 else 0.0

        # Consistency (are the collected OIDs consistent?)
        consistency = 1.0 if len(collected_oids) > 0 else 0.0

        return (coverage * 0.5 + completeness * 0.3 + consistency * 0.2)

    def _record_method_performance(self, method: CollectionMethod, result: StrategyResult, device_host: str):
        """Record method performance for learning."""
        perf = self.method_performance[method.value]

        # Update success rate
        current_success_rate = perf["success_rate"]
        perf["usage_count"] += 1

        # Calculate new success rate using exponential moving average
        alpha = 0.1  # Learning rate
        new_success = 1.0 if result.success else 0.0
        perf["success_rate"] = alpha * new_success + (1 - alpha) * current_success_rate

        # Update response time
        if result.execution_time_ms > 0:
            current_time = perf["avg_response_time"]
            perf["avg_response_time"] = alpha * result.execution_time_ms + (1 - alpha) * current_time

        # Update data quality
        if result.data_quality_score > 0:
            current_quality = perf["avg_data_quality"]
            perf["avg_data_quality"] = alpha * result.data_quality_score + (1 - alpha) * current_quality

        logger.debug(f"Updated performance for {method.value} on {device_host}: "
                    f"success_rate={perf['success_rate']:.2f}, "
                    f"avg_time={perf['avg_response_time']:.1f}ms")

    def _update_device_preferences(self, device_host: str, results: List[StrategyResult]):
        """Update device preferences based on collection results."""
        device_key = device_host  # Simplified for now

        # Find most successful method
        successful_results = [r for r in results if r.success and r.collected_oids]
        if successful_results:
            # Find method with best data quality
            best_result = max(successful_results, key=lambda r: r.data_quality_score)
            preferred_method = best_result.method

            # Update preferences
            if device_key not in self.device_preferences:
                self.device_preferences[device_key] = {}

            self.device_preferences[device_key].update({
                "preferred_method": preferred_method,
                "last_success": time.time(),
                "best_data_quality": best_result.data_quality_score
            })

            # Adjust timeout based on performance
            avg_time = sum(r.execution_time_ms for r in successful_results) / len(successful_results)
            if avg_time > 1000:  # Slow device
                self.device_preferences[device_key]["timeout_multiplier"] = 2.0
            elif avg_time < 100:  # Fast device
                self.device_preferences[device_key]["timeout_multiplier"] = 0.5

    async def _extract_method_data(self, result: StrategyResult, target: SNMPTarget) -> Dict[str, Any]:
        """Extract actual data from a method result."""
        # This would need to be implemented based on how we store method results
        # For now, return empty dict as placeholder
        return {}

    def get_method_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics for all methods."""
        return dict(self.method_performance)

    def get_device_preferences(self, device_host: str) -> Dict[str, Any]:
        """Get preferences for a specific device."""
        return self.device_preferences.get(device_host, {})

    async def close(self):
        """Close fallback strategies and cleanup resources."""
        await self.snmp_engine.close()
        await self.oid_explorer.close()