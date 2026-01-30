"""
Self-Learning Engine - Clustering and learning from device patterns.

This module implements machine learning-like capabilities to cluster similar
devices, learn from successful collections, and improve over time.
"""

import asyncio
import logging
import json
import time
import math
from typing import Dict, List, Set, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from pathlib import Path
import hashlib
import pickle

from ..core.engine import SNMPEngine, SNMPTarget
from ..intelligence.knowledge_base import KnowledgeBase, DeviceProfile
from ..intelligence.oid_explorer import OIDNode
from ..intelligence.pattern_recognition import PatternMatcher, ClassificationResult

logger = logging.getLogger(__name__)


@dataclass
class DeviceCluster:
    """Represents a cluster of similar devices."""
    cluster_id: str
    cluster_name: str
    device_ids: List[str] = field(default_factory=list)
    common_oids: List[str] = field(default_factory=list)
    vendor_hints: List[str] = field(default_factory=list)
    device_type_hints: List[str] = field(default_factory=list)
    collection_patterns: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    created_time: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningInstance:
    """Represents a learning instance from device interaction."""
    instance_id: str
    device_id: str
    timestamp: float
    device_signature: Dict[str, Any]
    discovered_oids: List[str]
    collection_results: Dict[str, Any]
    success_indicators: Dict[str, bool]
    performance_metrics: Dict[str, float]
    adaptations_applied: List[str] = field(default_factory=list)
    outcome_score: float = 0.0


@dataclass
class PatternMatch:
    """Represents a pattern match learned from data."""
    pattern_id: str
    pattern_type: str  # oid_structure, response_pattern, timing_pattern
    pattern_data: Dict[str, Any]
    confidence: float
    success_rate: float
    usage_count: int = 0
    last_used: float = 0.0


class DeviceSimilarityCalculator:
    """Calculates similarity between devices for clustering."""

    def __init__(self):
        """Initialize similarity calculator."""
        self.oid_weights = {
            "system_oids": 0.3,      # System information OIDs
            "vendor_oids": 0.4,       # Vendor-specific OIDs
            "performance_oids": 0.2,   # Performance monitoring OIDs
            "interface_oids": 0.1      # Interface OIDs
        }

    def calculate_device_similarity(
        self,
        device1_data: Dict[str, Any],
        device2_data: Dict[str, Any]
    ) -> float:
        """
        Calculate similarity between two devices.

        Args:
            device1_data: First device data
            device2_data: Second device data

        Returns:
            Similarity score (0.0 to 1.0)
        """
        total_score = 0.0
        total_weight = 0.0

        # Vendor similarity
        vendor_similarity = self._calculate_vendor_similarity(device1_data, device2_data)
        total_score += vendor_similarity * 0.3
        total_weight += 0.3

        # OID structure similarity
        oid_similarity = self._calculate_oid_similarity(device1_data, device2_data)
        total_score += oid_similarity * 0.5
        total_weight += 0.5

        # Response pattern similarity
        response_similarity = self._calculate_response_pattern_similarity(device1_data, device2_data)
        total_score += response_similarity * 0.2
        total_weight += 0.2

        return total_score / total_weight if total_weight > 0 else 0.0

    def _calculate_vendor_similarity(self, device1: Dict[str, Any], device2: Dict[str, Any]) -> float:
        """Calculate vendor similarity."""
        vendor1 = device1.get("vendor", "").lower()
        vendor2 = device2.get("vendor", "").lower()

        if vendor1 and vendor2:
            if vendor1 == vendor2:
                return 1.0
            elif self._are_vendors_related(vendor1, vendor2):
                return 0.7
            else:
                return 0.0
        elif vendor1 or vendor2:
            return 0.2  # One has vendor info, other doesn't
        else:
            return 0.0  # Neither has vendor info

    def _are_vendors_related(self, vendor1: str, vendor2: str) -> bool:
        """Check if two vendors are related."""
        # Related vendor groups
        related_groups = [
            ["huawei", "h3c", "hpe"],
            ["zte", "zte corporation"],
            ["cisco", "cisco systems"],
            ["vsol", "volution"],
        ]

        for group in related_groups:
            if vendor1 in group and vendor2 in group:
                return True

        return False

    def _calculate_oid_similarity(self, device1: Dict[str, Any], device2: Dict[str, Any]) -> float:
        """Calculate OID structure similarity."""
        oids1 = set(device1.get("discovered_oids", []))
        oids2 = set(device2.get("discovered_oids", []))

        if not oids1 or not oids2:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(oids1 & oids2)
        union = len(oids1 | oids2)

        base_similarity = intersection / union if union > 0 else 0.0

        # Weight different types of OIDs
        weighted_similarity = self._apply_oid_weights(oids1, oids2, base_similarity)

        return weighted_similarity

    def _apply_oid_weights(self, oids1: Set[str], oids2: Set[str], base_similarity: float) -> float:
        """Apply weights to different OID categories."""
        category_similarities = []

        for category, weight in self.oid_weights.items():
            category_oids1 = self._filter_oids_by_category(oids1, category)
            category_oids2 = self._filter_oids_by_category(oids2, category)

            if category_oids1 and category_oids2:
                intersection = len(category_oids1 & category_oids2)
                union = len(category_oids1 | category_oids2)
                category_similarity = intersection / union if union > 0 else 0.0
                category_similarities.append(category_similarity * weight)
            elif category_oids1 or category_oids2:
                category_similarities.append(0.0)  # No match in this category

        return sum(category_similarities) if category_similarities else base_similarity

    def _filter_oids_by_category(self, oids: Set[str], category: str) -> Set[str]:
        """Filter OIDs by category."""
        filtered = set()

        for oid in oids:
            if category == "system_oids" and "1.3.6.1.2.1.1" in oid:
                filtered.add(oid)
            elif category == "vendor_oids" and "1.3.6.1.4.1" in oid:
                filtered.add(oid)
            elif category == "performance_oids" and any(
                keyword in oid.lower() for keyword in ["cpu", "memory", "temp", "usage"]
            ):
                filtered.add(oid)
            elif category == "interface_oids" and "1.3.6.1.2.1.2" in oid:
                filtered.add(oid)

        return filtered

    def _calculate_response_pattern_similarity(self, device1: Dict[str, Any], device2: Dict[str, Any]) -> float:
        """Calculate response pattern similarity."""
        patterns1 = device1.get("response_patterns", {})
        patterns2 = device2.get("response_patterns", {})

        if not patterns1 or not patterns2:
            return 0.0

        # Compare response times
        time1 = patterns1.get("avg_response_time_ms", 50)
        time2 = patterns2.get("avg_response_time_ms", 50)

        time_similarity = 1.0 - min(abs(time1 - time2) / max(time1, time2), 1.0)

        # Compare error rates
        error1 = patterns1.get("error_rate", 0.0)
        error2 = patterns2.get("error_rate", 0.0)

        error_similarity = 1.0 - abs(error1 - error2)

        # Compare success rates
        success1 = patterns1.get("success_rate", 1.0)
        success2 = patterns2.get("success_rate", 1.0)

        success_similarity = 1.0 - abs(success1 - success2)

        return (time_similarity + error_similarity + success_similarity) / 3


class SelfLearningEngine:
    """
    Self-learning engine for device clustering and pattern recognition.

    Features:
    - Automatic device clustering based on similarity
    - Pattern learning from successful collections
    - Adaptation strategy optimization
    - Knowledge extraction from collected data
    - Performance improvement over time
    """

    def __init__(self, data_dir: str = "learning_data"):
        """
        Initialize self-learning engine.

        Args:
            data_dir: Directory to store learning data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Components
        self.similarity_calculator = DeviceSimilarityCalculator()
        self.pattern_recognition = PatternRecognition()

        # Storage
        self.clusters: Dict[str, DeviceCluster] = {}
        self.learning_instances: Dict[str, LearningInstance] = {}
        self.learned_patterns: Dict[str, PatternMatch] = {}

        # Learning parameters
        self.learning_params = {
            "similarity_threshold": 0.7,      # Minimum similarity for clustering
            "min_cluster_size": 2,            # Minimum devices to form a cluster
            "pattern_confidence_threshold": 0.6,  # Minimum confidence for learned patterns
            "adaptation_success_threshold": 0.8,  # Success rate for adaptation adoption
            "max_learning_instances": 10000,   # Maximum learning instances to keep
            "cluster_update_interval": 3600,   # Update clusters every hour
        }

        # Statistics
        self.stats = {
            "total_clusters": 0,
            "total_learning_instances": 0,
            "total_learned_patterns": 0,
            "successful_adaptations": 0,
            "avg_cluster_quality": 0.0,
            "last_update": time.time()
        }

        # Load existing learning data
        self._load_learning_data()

    async def learn_from_device(
        self,
        device_id: str,
        device_signature: Dict[str, Any],
        discovered_oids: List[str],
        collection_results: Dict[str, Any],
        performance_metrics: Dict[str, Any]
    ) -> str:
        """
        Learn from a device interaction.

        Args:
            device_id: Device identifier
            device_signature: Device signature
            discovered_oids: List of discovered OIDs
            collection_results: Collection results
            performance_metrics: Performance metrics

        Returns:
            Learning instance ID
        """
        logger.info(f"Learning from device: {device_id}")

        # Create learning instance
        instance = LearningInstance(
            instance_id=self._generate_instance_id(device_id),
            device_id=device_id,
            timestamp=time.time(),
            device_signature=device_signature,
            discovered_oids=discovered_oids,
            collection_results=collection_results,
            success_indicators=self._extract_success_indicators(collection_results),
            performance_metrics=performance_metrics,
            outcome_score=self._calculate_outcome_score(collection_results, performance_metrics)
        )

        # Store learning instance
        self.learning_instances[instance.instance_id] = instance
        self.stats["total_learning_instances"] += 1

        # Update clusters if needed
        await self._update_clusters_with_device(instance)

        # Extract patterns from this instance
        await self._extract_patterns_from_instance(instance)

        # Clean up old instances if needed
        self._cleanup_old_instances()

        # Save learning data
        self._save_learning_data()

        logger.info(f"Created learning instance: {instance.instance_id}")
        return instance.instance_id

    async def find_similar_devices(
        self,
        target_device_data: Dict[str, Any],
        max_results: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Find devices similar to the target device.

        Args:
            target_device_data: Target device data
            max_results: Maximum number of results

        Returns:
            List of (device_id, similarity_score) tuples
        """
        similarities = []

        for instance_id, instance in self.learning_instances.items():
            # Build device data from learning instance
            device_data = {
                "vendor": instance.device_signature.get("vendor"),
                "discovered_oids": instance.discovered_oids,
                "response_patterns": {
                    "avg_response_time_ms": instance.performance_metrics.get("response_time_ms", 50),
                    "error_rate": 1.0 - instance.outcome_score,
                    "success_rate": instance.outcome_score
                }
            }

            similarity = self.similarity_calculator.calculate_device_similarity(
                target_device_data, device_data
            )

            if similarity > 0.3:  # Minimum similarity threshold
                similarities.append((instance.device_id, similarity))

        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:max_results]

    async def recommend_collection_strategy(
        self,
        device_id: str,
        device_signature: Dict[str, Any],
        discovered_oids: List[str]
    ) -> Dict[str, Any]:
        """
        Recommend collection strategy based on learning.

        Args:
            device_id: Device identifier
            device_signature: Device signature
            discovered_oids: Discovered OIDs

        Returns:
            Recommended collection strategy
        """
        # Find similar devices
        target_data = {
            "vendor": device_signature.get("vendor"),
            "discovered_oids": discovered_oids
        }

        similar_devices = await self.find_similar_devices(target_data, max_results=5)

        if not similar_devices:
            return self._get_default_strategy()

        # Analyze successful strategies from similar devices
        strategies = []
        for similar_device_id, similarity in similar_devices:
            # Find learning instances for this device
            device_instances = [
                instance for instance in self.learning_instances.values()
                if instance.device_id == similar_device_id and instance.outcome_score > 0.7
            ]

            if device_instances:
                # Extract successful strategies
                for instance in device_instances:
                    strategy = self._extract_strategy_from_instance(instance)
                    if strategy:
                        strategies.append((strategy, similarity * instance.outcome_score))

        if strategies:
            # Weight strategies by similarity and success
            weighted_strategies = defaultdict(lambda: {"weight": 0.0, "count": 0})

            for strategy, weight in strategies:
                for key, value in strategy.items():
                    if isinstance(value, (int, float)):
                        weighted_strategies[key]["weight"] += value * weight
                        weighted_strategies[key]["count"] += 1

            # Calculate weighted average
            recommended_strategy = {}
            for key, data in weighted_strategies.items():
                recommended_strategy[key] = data["weight"] / data["count"]

            logger.info(f"Recommended strategy for {device_id} based on {len(strategies)} similar devices")
            return recommended_strategy

        return self._get_default_strategy()

    async def get_device_clusters(self) -> Dict[str, DeviceCluster]:
        """Get all device clusters."""
        return self.clusters.copy()

    async def get_cluster_insights(self, cluster_id: str) -> Dict[str, Any]:
        """
        Get insights about a specific cluster.

        Args:
            cluster_id: Cluster ID

        Returns:
            Cluster insights
        """
        cluster = self.clusters.get(cluster_id)
        if not cluster:
            return {}

        insights = {
            "cluster_info": {
                "id": cluster.cluster_id,
                "name": cluster.cluster_name,
                "device_count": len(cluster.device_ids),
                "confidence": cluster.confidence_score,
                "created": cluster.created_time,
                "last_updated": cluster.last_updated
            },
            "vendor_analysis": dict(Counter(cluster.vendor_hints)),
            "device_type_analysis": dict(Counter(cluster.device_type_hints)),
            "common_capabilities": [],
            "performance_profile": {},
            "recommended_strategies": {}
        }

        # Analyze common capabilities
        if cluster.common_oids:
            insights["common_capabilities"] = self._analyze_common_oids(cluster.common_oids)

        # Analyze performance profile
        instances_in_cluster = [
            instance for instance in self.learning_instances.values()
            if instance.device_id in cluster.device_ids
        ]

        if instances_in_cluster:
            insights["performance_profile"] = self._analyze_cluster_performance(instances_in_cluster)
            insights["recommended_strategies"] = self._extract_cluster_strategies(instances_in_cluster)

        return insights

    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning engine statistics."""
        self.stats["total_clusters"] = len(self.clusters)
        self.stats["total_learned_patterns"] = len(self.learned_patterns)

        if self.clusters:
            avg_quality = sum(cluster.confidence_score for cluster in self.clusters.values()) / len(self.clusters)
            self.stats["avg_cluster_quality"] = avg_quality

        return self.stats.copy()

    async def _update_clusters_with_device(self, instance: LearningInstance):
        """Update clusters with a new device instance."""
        # Find best matching cluster
        best_cluster = None
        best_similarity = 0.0

        for cluster in self.clusters.values():
            # Calculate similarity to cluster
            cluster_similarity = self._calculate_cluster_similarity(instance, cluster)
            if cluster_similarity > best_similarity:
                best_similarity = cluster_similarity
                best_cluster = cluster

        # Check if device fits in existing cluster
        if best_cluster and best_similarity > self.learning_params["similarity_threshold"]:
            # Add to existing cluster
            best_cluster.device_ids.append(instance.device_id)
            best_cluster.last_updated = time.time()
            self._update_cluster_characteristics(best_cluster)
            logger.debug(f"Added device {instance.device_id} to cluster {best_cluster.cluster_id}")
        else:
            # Create new cluster if similar devices exist
            similar_devices = await self.find_similar_devices({
                "vendor": instance.device_signature.get("vendor"),
                "discovered_oids": instance.discovered_oids
            }, max_results=10)

            similar_count = len([d for d, s in similar_devices if s > self.learning_params["similarity_threshold"]])

            if similar_count >= self.learning_params["min_cluster_size"] - 1:
                # Create new cluster
                new_cluster = await self._create_cluster_from_device(instance)
                self.clusters[new_cluster.cluster_id] = new_cluster
                logger.info(f"Created new cluster: {new_cluster.cluster_id}")

    async def _create_cluster_from_device(self, instance: LearningInstance) -> DeviceCluster:
        """Create a new cluster from a device instance."""
        cluster_id = self._generate_cluster_id(instance)
        cluster_name = f"{instance.device_signature.get('vendor', 'unknown')}_cluster"

        cluster = DeviceCluster(
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            device_ids=[instance.device_id],
            common_oids=instance.discovered_oids.copy(),
            vendor_hints=[instance.device_signature.get("vendor", "unknown")],
            device_type_hints=[instance.device_signature.get("device_type", "unknown")],
            collection_patterns=self._extract_collection_patterns(instance),
            confidence_score=instance.outcome_score
        )

        return cluster

    def _calculate_cluster_similarity(self, instance: LearningInstance, cluster: DeviceCluster) -> float:
        """Calculate similarity between device instance and cluster."""
        # Find representative instances from cluster
        cluster_instances = [
            inst for inst in self.learning_instances.values()
            if inst.device_id in cluster.device_ids
        ]

        if not cluster_instances:
            return 0.0

        # Calculate average similarity to cluster instances
        similarities = []
        for cluster_instance in cluster_instances:
            instance_data = {
                "vendor": instance.device_signature.get("vendor"),
                "discovered_oids": instance.discovered_oids,
                "response_patterns": {
                    "avg_response_time_ms": instance.performance_metrics.get("response_time_ms", 50),
                    "success_rate": instance.outcome_score
                }
            }

            cluster_data = {
                "vendor": cluster_instance.device_signature.get("vendor"),
                "discovered_oids": cluster_instance.discovered_oids,
                "response_patterns": {
                    "avg_response_time_ms": cluster_instance.performance_metrics.get("response_time_ms", 50),
                    "success_rate": cluster_instance.outcome_score
                }
            }

            similarity = self.similarity_calculator.calculate_device_similarity(instance_data, cluster_data)
            similarities.append(similarity)

        return sum(similarities) / len(similarities) if similarities else 0.0

    def _update_cluster_characteristics(self, cluster: DeviceCluster):
        """Update cluster characteristics based on current members."""
        instances = [
            inst for inst in self.learning_instances.values()
            if inst.device_id in cluster.device_ids
        ]

        if not instances:
            return

        # Update common OIDs (intersection of all devices)
        common_oids = set(instances[0].discovered_oids)
        for instance in instances[1:]:
            common_oids &= set(instance.discovered_oids)
        cluster.common_oids = list(common_oids)

        # Update vendor hints
        vendors = [inst.device_signature.get("vendor", "unknown") for inst in instances]
        cluster.vendor_hints = list(set(vendors))

        # Update device type hints
        device_types = [inst.device_signature.get("device_type", "unknown") for inst in instances]
        cluster.device_type_hints = list(set(device_types))

        # Update confidence score (average of member scores)
        cluster.confidence_score = sum(inst.outcome_score for inst in instances) / len(instances)

        # Update collection patterns
        patterns = [self._extract_collection_patterns(inst) for inst in instances]
        cluster.collection_patterns = self._merge_collection_patterns(patterns)

    def _extract_success_indicators(self, collection_results: Dict[str, Any]) -> Dict[str, bool]:
        """Extract success indicators from collection results."""
        indicators = {}

        indicators["data_collected"] = bool(collection_results.get("data"))
        indicators["no_errors"] = not collection_results.get("errors", [])
        indicators["complete_collection"] = collection_results.get("collection_complete", False)
        indicators["reasonable_response_time"] = collection_results.get("response_time_ms", 0) < 5000

        return indicators

    def _calculate_outcome_score(
        self,
        collection_results: Dict[str, Any],
        performance_metrics: Dict[str, Any]
    ) -> float:
        """Calculate outcome score for a learning instance."""
        score = 0.0

        # Success indicators (40% weight)
        success_indicators = self._extract_success_indicators(collection_results)
        success_score = sum(success_indicators.values()) / len(success_indicators)
        score += success_score * 0.4

        # Performance metrics (30% weight)
        response_time = performance_metrics.get("response_time_ms", 50)
        time_score = max(0, 1.0 - (response_time - 50) / 1000)  # Penalty for slow responses
        score += time_score * 0.3

        # Data quality (30% weight)
        data = collection_results.get("data", {})
        if isinstance(data, dict):
            data_quality = min(1.0, len(data) / 20)  # Assume 20 data points is good
            score += data_quality * 0.3

        return min(score, 1.0)

    async def _extract_patterns_from_instance(self, instance: LearningInstance):
        """Extract patterns from a learning instance."""
        # OID structure patterns
        await self._extract_oid_structure_patterns(instance)

        # Response patterns
        await self._extract_response_patterns(instance)

        # Timing patterns
        await self._extract_timing_patterns(instance)

    async def _extract_oid_structure_patterns(self, instance: LearningInstance):
        """Extract OID structure patterns."""
        if not instance.discovered_oids:
            return

        # Analyze OID prefixes
        prefixes = defaultdict(int)
        for oid in instance.discovered_oids:
            parts = oid.split('.')
            if len(parts) >= 6:
                prefix = '.'.join(parts[:6])
                prefixes[prefix] += 1

        # Create pattern for common prefixes
        for prefix, count in prefixes.items():
            if count >= 3:  # At least 3 OIDs with same prefix
                pattern_id = f"oid_prefix_{hashlib.md5(prefix.encode()).hexdigest()[:8]}"

                pattern = PatternMatch(
                    pattern_id=pattern_id,
                    pattern_type="oid_structure",
                    pattern_data={
                        "prefix": prefix,
                        "oid_count": count,
                        "vendor": instance.device_signature.get("vendor"),
                        "device_type": instance.device_signature.get("device_type")
                    },
                    confidence=instance.outcome_score,
                    success_rate=1.0 if instance.outcome_score > 0.7 else 0.0
                )

                self.learned_patterns[pattern_id] = pattern

    async def _extract_response_patterns(self, instance: LearningInstance):
        """Extract response patterns."""
        # This would analyze patterns in SNMP responses
        # For now, just store basic response information
        pass

    async def _extract_timing_patterns(self, instance: LearningInstance):
        """Extract timing patterns."""
        response_time = instance.performance_metrics.get("response_time_ms", 0)

        pattern_id = f"timing_{instance.device_signature.get('vendor', 'unknown')}_{hashlib.md5(str(response_time).encode()).hexdigest()[:8]}"

        pattern = PatternMatch(
            pattern_id=pattern_id,
            pattern_type="timing_pattern",
            pattern_data={
                "avg_response_time_ms": response_time,
                "vendor": instance.device_signature.get("vendor"),
                "device_type": instance.device_signature.get("device_type")
            },
            confidence=instance.outcome_score,
            success_rate=1.0 if instance.outcome_score > 0.7 else 0.0
        )

        self.learned_patterns[pattern_id] = pattern

    def _extract_collection_patterns(self, instance: LearningInstance) -> Dict[str, Any]:
        """Extract collection patterns from instance."""
        return {
            "avg_response_time_ms": instance.performance_metrics.get("response_time_ms", 50),
            "success_rate": instance.outcome_score,
            "preferred_method": "get_bulk" if instance.outcome_score > 0.8 else "get_next",
            "concurrent_requests": max(1, int(1000 / max(1, instance.performance_metrics.get("response_time_ms", 50)))),
            "timeout": max(3, int(instance.performance_metrics.get("response_time_ms", 50) / 100)),
        }

    def _merge_collection_patterns(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple collection patterns."""
        if not patterns:
            return {}

        merged = {
            "avg_response_time_ms": sum(p.get("avg_response_time_ms", 50) for p in patterns) / len(patterns),
            "success_rate": sum(p.get("success_rate", 0) for p in patterns) / len(patterns),
            "concurrent_requests": int(sum(p.get("concurrent_requests", 5) for p in patterns) / len(patterns)),
            "timeout": int(sum(p.get("timeout", 5) for p in patterns) / len(patterns)),
        }

        # Determine preferred method
        methods = [p.get("preferred_method", "get") for p in patterns]
        if methods.count("get_bulk") > len(methods) / 2:
            merged["preferred_method"] = "get_bulk"
        else:
            merged["preferred_method"] = "get_next"

        return merged

    def _cleanup_old_instances(self):
        """Clean up old learning instances to prevent memory bloat."""
        if len(self.learning_instances) > self.learning_params["max_learning_instances"]:
            # Sort by timestamp and keep the most recent ones
            sorted_instances = sorted(
                self.learning_instances.items(),
                key=lambda x: x[1].timestamp,
                reverse=True
            )

            # Keep only the most recent instances
            keep_count = self.learning_params["max_learning_instances"]
            self.learning_instances = dict(sorted_instances[:keep_count])

            logger.info(f"Cleaned up old learning instances, keeping {keep_count} most recent")

    def _generate_instance_id(self, device_id: str) -> str:
        """Generate unique learning instance ID."""
        content = f"{device_id}_{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _generate_cluster_id(self, instance: LearningInstance) -> str:
        """Generate unique cluster ID."""
        content = f"{instance.device_signature.get('vendor', 'unknown')}_{instance.device_signature.get('device_type', 'unknown')}_{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _get_default_strategy(self) -> Dict[str, Any]:
        """Get default collection strategy."""
        return {
            "method": "get_bulk",
            "max_repetitions": 20,
            "concurrent_requests": 10,
            "timeout": 5,
            "retries": 3
        }

    def _extract_strategy_from_instance(self, instance: LearningInstance) -> Optional[Dict[str, Any]]:
        """Extract collection strategy from a learning instance."""
        if instance.outcome_score > 0.7:  # Only extract from successful instances
            return self._extract_collection_patterns(instance)
        return None

    def _analyze_common_oids(self, oids: List[str]) -> List[Dict[str, Any]]:
        """Analyze common OIDs in a cluster."""
        # Group OIDs by category
        categories = defaultdict(list)
        for oid in oids:
            if "1.3.6.1.2.1.1" in oid:
                categories["system"].append(oid)
            elif "1.3.6.1.2.1.2" in oid:
                categories["interfaces"].append(oid)
            elif "4.1.2011" in oid:
                categories["huawei_specific"].append(oid)
            elif "4.1.3902" in oid:
                categories["zte_specific"].append(oid)
            elif "4.1.39926" in oid:
                categories["vsol_specific"].append(oid)

        return [
            {"category": cat, "oids": oid_list, "count": len(oid_list)}
            for cat, oid_list in categories.items()
        ]

    def _analyze_cluster_performance(self, instances: List[LearningInstance]) -> Dict[str, Any]:
        """Analyze performance profile of a cluster."""
        if not instances:
            return {}

        response_times = [inst.performance_metrics.get("response_time_ms", 50) for inst in instances]
        outcome_scores = [inst.outcome_score for inst in instances]

        return {
            "avg_response_time_ms": sum(response_times) / len(response_times),
            "min_response_time_ms": min(response_times),
            "max_response_time_ms": max(response_times),
            "avg_success_rate": sum(outcome_scores) / len(outcome_scores),
            "most_successful_method": "get_bulk" if sum(outcome_scores) / len(outcome_scores) > 0.8 else "get_next",
            "sample_size": len(instances)
        }

    def _extract_cluster_strategies(self, instances: List[LearningInstance]) -> Dict[str, Any]:
        """Extract optimal strategies for a cluster."""
        successful_instances = [inst for inst in instances if inst.outcome_score > 0.7]

        if not successful_instances:
            return self._get_default_strategy()

        strategies = [self._extract_collection_patterns(inst) for inst in successful_instances]
        return self._merge_collection_patterns(strategies)

    def _load_learning_data(self):
        """Load existing learning data from disk."""
        # Load clusters
        clusters_file = self.data_dir / "clusters.pkl"
        if clusters_file.exists():
            try:
                with open(clusters_file, 'rb') as f:
                    self.clusters = pickle.load(f)
                logger.info(f"Loaded {len(self.clusters)} clusters")
            except Exception as e:
                logger.error(f"Failed to load clusters: {e}")

        # Load learning instances
        instances_file = self.data_dir / "instances.pkl"
        if instances_file.exists():
            try:
                with open(instances_file, 'rb') as f:
                    self.learning_instances = pickle.load(f)
                logger.info(f"Loaded {len(self.learning_instances)} learning instances")
            except Exception as e:
                logger.error(f"Failed to load learning instances: {e}")

        # Load learned patterns
        patterns_file = self.data_dir / "patterns.pkl"
        if patterns_file.exists():
            try:
                with open(patterns_file, 'rb') as f:
                    self.learned_patterns = pickle.load(f)
                logger.info(f"Loaded {len(self.learned_patterns)} learned patterns")
            except Exception as e:
                logger.error(f"Failed to load learned patterns: {e}")

    def _save_learning_data(self):
        """Save learning data to disk."""
        try:
            # Save clusters
            clusters_file = self.data_dir / "clusters.pkl"
            with open(clusters_file, 'wb') as f:
                pickle.dump(self.clusters, f)

            # Save learning instances
            instances_file = self.data_dir / "instances.pkl"
            with open(instances_file, 'wb') as f:
                pickle.dump(self.learning_instances, f)

            # Save learned patterns
            patterns_file = self.data_dir / "patterns.pkl"
            with open(patterns_file, 'wb') as f:
                pickle.dump(self.learned_patterns, f)

            logger.debug("Learning data saved to disk")
        except Exception as e:
            logger.error(f"Failed to save learning data: {e}")

    async def close(self):
        """Close self-learning engine and cleanup resources."""
        self._save_learning_data()
        logger.info("Self-learning engine closed")