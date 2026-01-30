"""
Enhanced Device class with all advanced features integrated.

This module brings together all the intelligence, adaptive, and self-learning
capabilities into a unified device management system.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import json
import time

from .engine import SNMPEngine, SNMPTarget, SNMPVersion
from .device import Device, DeviceStatus, DeviceMetrics
from ..intelligence.oid_explorer import OIDExplorer
from ..intelligence.reverse_engineer import ReverseEngineer, ReverseEngineeringResult
from ..intelligence.knowledge_base import KnowledgeBase, DeviceProfile
from ..intelligence.pattern_recognition import PatternMatcher, ClassificationResult
from ..adaptive.adapter_generator import AdapterGenerator
from ..adaptive.self_learning import SelfLearningEngine
from ..adaptive.fallback_strategies import FallbackStrategies

logger = logging.getLogger(__name__)


class EnhancedDevice(Device):
    """
    Enhanced device with all advanced features.

    Features:
    - Intelligent OID exploration and discovery
    - Reverse engineering of undocumented devices
    - Pattern recognition and device classification
    - Dynamic adapter generation
    - Self-learning from device interactions
    - Multiple fallback strategies
    - Knowledge base integration
    """

    def __init__(self, *args, **kwargs):
        """Initialize enhanced device."""
        super().__init__(*args, **kwargs)

        # Advanced components
        self.oid_explorer = OIDExplorer(self.snmp_engine)
        self.reverse_engineer = ReverseEngineer(self.snmp_engine)
        self.knowledge_base = KnowledgeBase()
        self.pattern_recognition = PatternRecognition()
        self.adapter_generator = AdapterGenerator(self.knowledge_base)
        self.self_learning = SelfLearningEngine()
        self.fallback_strategies = FallbackStrategies(self.snmp_engine)

        # Enhanced state
        self.explored_oids: Dict[str, Any] = {}
        self.reverse_engineered_data: Optional[ReverseEngineeringResult] = None
        self.generated_adapter = None
        self.device_profile: Optional[DeviceProfile] = None
        self.learning_history: List[str] = []  # Learning instance IDs
        self.collection_strategy = "adaptive"

        # Performance tracking
        self.advanced_metrics = {
            "oid_exploration_time": 0.0,
            "reverse_engineering_time": 0.0,
            "pattern_classification_time": 0.0,
            "adapter_generation_time": 0.0,
            "total_discovery_time": 0.0
        }

    async def intelligent_discover(self) -> Dict[str, Any]:
        """
        Perform intelligent device discovery using all advanced features.

        Returns:
            Comprehensive discovery results
        """
        logger.info(f"Starting intelligent discovery for {self.host}")
        start_time = time.time()

        discovery_results = {
            "device_id": f"{self.host}:{self.port}",
            "discovery_timestamp": datetime.now().isoformat(),
            "stages": {},
            "final_profile": None,
            "generated_adapter": None,
            "learning_insights": {}
        }

        # Stage 1: OID Exploration
        logger.info("Stage 1: OID Exploration")
        exploration_start = time.time()
        target = SNMPTarget(
            host=self.host,
            port=self.port,
            timeout=self.timeout,
            retries=self.retries
        )
        target.credentials = self.target.credentials

        try:
            self.explored_oids = await self.oid_explorer.explore_device(target)
            discovery_results["stages"]["oid_exploration"] = {
                "success": True,
                "oids_discovered": len(self.explored_oids),
                "duration_ms": (time.time() - exploration_start) * 1000
            }
        except Exception as e:
            logger.error(f"OID exploration failed: {e}")
            discovery_results["stages"]["oid_exploration"] = {
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - exploration_start) * 1000
            }

        self.advanced_metrics["oid_exploration_time"] = (time.time() - exploration_start) * 1000

        # Stage 2: Pattern Recognition
        logger.info("Stage 2: Pattern Recognition")
        pattern_start = time.time()
        try:
            # Create basic system info from explored OIDs
            system_info = self._extract_system_info_from_oids(self.explored_oids)

            classification = self.pattern_recognition.classify_device(
                device_id=f"{self.host}:{self.port}",
                oid_tree=self.explored_oids,
                system_info=system_info
            )

            discovery_results["stages"]["pattern_recognition"] = {
                "success": True,
                "classification": {
                    "vendor": classification.vendor,
                    "device_type": classification.device_type,
                    "model": classification.model,
                    "confidence": classification.confidence
                },
                "duration_ms": (time.time() - pattern_start) * 1000
            }

            # Update device signature
            if classification.confidence > 0.5:
                self.signature = type(self.signature)(
                    vendor=classification.vendor,
                    device_type=classification.device_type,
                    model=classification.model,
                    firmware_version=None,
                    confidence=classification.confidence,
                    evidence=classification.evidence
                )

        except Exception as e:
            logger.error(f"Pattern recognition failed: {e}")
            discovery_results["stages"]["pattern_recognition"] = {
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - pattern_start) * 1000
            }

        self.advanced_metrics["pattern_classification_time"] = (time.time() - pattern_start) * 1000

        # Stage 3: Knowledge Base Lookup
        logger.info("Stage 3: Knowledge Base Lookup")
        kb_start = time.time()
        try:
            # Get device signature
            device_signature = {
                "vendor": self.signature.vendor.value if self.signature else "unknown",
                "device_type": self.signature.device_type.value if self.signature else "unknown",
                "model": self.signature.model if self.signature else "unknown"
            }

            # Look for matching profile
            profile = self.knowledge_base.get_profile_for_device(
                device_signature=device_signature,
                discovered_oids=list(self.explored_oids.keys()),
                vendor_hint=device_signature["vendor"]
            )

            if profile:
                self.device_profile = profile
                discovery_results["stages"]["knowledge_base"] = {
                    "success": True,
                    "profile_found": profile.profile_id,
                    "profile_rating": profile.rating,
                    "profile_verified": profile.verified
                }
            else:
                discovery_results["stages"]["knowledge_base"] = {
                    "success": True,
                    "profile_found": None,
                    "message": "No matching profile found"
                }

        except Exception as e:
            logger.error(f"Knowledge base lookup failed: {e}")
            discovery_results["stages"]["knowledge_base"] = {
                "success": False,
                "error": str(e)
            }

        # Stage 4: Reverse Engineering (if needed)
        if not self.device_profile or (self.signature and self.signature.confidence < 0.7):
            logger.info("Stage 4: Reverse Engineering")
            re_start = time.time()
            try:
                vendor_hint = self.signature.vendor.value if self.signature else None
                self.reverse_engineered_data = await self.reverse_engineer.reverse_engineer_device(
                    target=target,
                    vendor_hint=vendor_hint,
                    max_time_seconds=60  # Limit to 1 minute
                )

                discovery_results["stages"]["reverse_engineering"] = {
                    "success": True,
                    "oids_discovered": len(self.reverse_engineered_data.discovered_oids),
                    "success_rate": self.reverse_engineered_data.success_rate,
                    "functionality_matrix": self.reverse_engineered_data.functionality_matrix,
                    "duration_ms": (time.time() - re_start) * 1000
                }

                # Create profile from reverse engineering results
                if self.reverse_engineered_data.success_rate > 0.5:
                    auto_profile = self._create_profile_from_reverse_engineering()
                    self.device_profile = auto_profile
                    discovery_results["stages"]["reverse_engineering"]["auto_profile_created"] = True

            except Exception as e:
                logger.error(f"Reverse engineering failed: {e}")
                discovery_results["stages"]["reverse_engineering"] = {
                    "success": False,
                    "error": str(e),
                    "duration_ms": (time.time() - re_start) * 1000
                }

            self.advanced_metrics["reverse_engineering_time"] = (time.time() - re_start) * 1000

        # Stage 5: Adapter Generation
        logger.info("Stage 5: Adapter Generation")
        adapter_start = time.time()
        try:
            if self.device_profile:
                self.generated_adapter = await self.adapter_generator.generate_adapter_from_profile(
                    profile=self.device_profile,
                    validation_target=target
                )
            elif self.explored_oids:
                # Generate from exploration results
                self.generated_adapter = await self.adapter_generator.generate_adapter_from_discovery(
                    vendor=self.signature.vendor.value if self.signature else "unknown",
                    device_type=self.signature.device_type.value if self.signature else "unknown",
                    discovered_oids=self.explored_oids,
                    system_info=self._extract_system_info_from_oids(self.explored_oids),
                    validation_target=target
                )

            if self.generated_adapter:
                discovery_results["stages"]["adapter_generation"] = {
                    "success": True,
                    "adapter_name": self.generated_adapter.name,
                    "oid_mappings": len(self.generated_adapter.oid_mappings),
                    "transform_rules": len(self.generated_adapter.transforms),
                    "duration_ms": (time.time() - adapter_start) * 1000
                }
                discovery_results["generated_adapter"] = asdict(self.generated_adapter)
            else:
                discovery_results["stages"]["adapter_generation"] = {
                    "success": False,
                    "message": "No adapter generated"
                }

        except Exception as e:
            logger.error(f"Adapter generation failed: {e}")
            discovery_results["stages"]["adapter_generation"] = {
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - adapter_start) * 1000
            }

        self.advanced_metrics["adapter_generation_time"] = (time.time() - adapter_start) * 1000

        # Calculate total discovery time
        self.advanced_metrics["total_discovery_time"] = (time.time() - start_time) * 1000
        discovery_results["total_duration_ms"] = self.advanced_metrics["total_discovery_time"]

        # Store final profile
        discovery_results["final_profile"] = asdict(self.device_profile) if self.device_profile else None

        logger.info(f"Intelligent discovery completed in {self.advanced_metrics['total_discovery_time']:.1f}ms")
        return discovery_results

    async def collect_with_intelligence(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Collect data using all intelligent features.

        Args:
            force_refresh: Ignore cache and force fresh collection

        Returns:
            Collected data with intelligence annotations
        """
        logger.info(f"Starting intelligent collection from {self.host}")
        start_time = time.time()

        # Check if we need to perform discovery first
        if not self.signature or not self.explored_oids:
            await self.intelligent_discover()

        # Prepare target
        target = SNMPTarget(
            host=self.host,
            port=self.port,
            timeout=self.timeout,
            retries=self.retries
        )
        target.credentials = self.target.credentials

        # Determine collection strategy
        if self.generated_adapter and self.generated_adapter.collection_strategy:
            strategy_name = "adaptive"  # Use adaptive to leverage adapter knowledge
        else:
            strategy_name = self.collection_strategy

        # Get OIDs to collect
        oids_to_collect = self._determine_oids_to_collect()

        # Use fallback strategies for collection
        collected_data, strategy_results = await self.fallback_strategies.collect_with_fallback(
            target=target,
            oids=oids_to_collect,
            strategy_name=strategy_name,
            device_signature={
                "vendor": self.signature.vendor.value if self.signature else "unknown",
                "device_type": self.signature.device_type.value if self.signature else "unknown"
            }
        )

        # Process collected data
        processed_data = await self._process_collected_data(collected_data, strategy_results)

        # Learn from this collection
        await self._learn_from_collection(processed_data, strategy_results)

        # Add intelligence metadata
        processed_data["intelligence"] = {
            "collection_method": "intelligent",
            "strategy_used": strategy_name,
            "strategy_results": [asdict(result) for result in strategy_results],
            "device_signature": asdict(self.signature) if self.signature else None,
            "generated_adapter": asdict(self.generated_adapter) if self.generated_adapter else None,
            "discovery_metrics": self.advanced_metrics,
            "learning_instances": len(self.learning_history)
        }

        # Update metrics
        self._update_intelligent_metrics(processed_data, strategy_results, time.time() - start_time)

        # Cache results
        self._cached_data = processed_data
        self._cache_timestamp = datetime.now()

        logger.info(f"Intelligent collection completed: {len(processed_data)} fields collected")
        return processed_data

    def _extract_system_info_from_oids(self, explored_oids: Dict[str, Any]) -> Dict[str, Any]:
        """Extract system information from explored OIDs."""
        system_info = {}

        # Look for system description
        sys_desc_oid = "1.3.6.1.2.1.1.1.0"
        if sys_desc_oid in explored_oids:
            system_info["description"] = "System description available"

        # Look for system name
        sys_name_oid = "1.3.6.1.2.1.1.5.0"
        if sys_name_oid in explored_oids:
            system_info["name"] = "System name available"

        # Look for uptime
        sys_uptime_oid = "1.3.6.1.2.1.1.3.0"
        if sys_uptime_oid in explored_oids:
            system_info["uptime"] = "System uptime available"

        return system_info

    def _create_profile_from_reverse_engineering(self) -> DeviceProfile:
        """Create a device profile from reverse engineering results."""
        if not self.reverse_engineered_data:
            return None

        re_data = self.reverse_engineered_data

        # Determine vendor and device type from functionality matrix
        vendor = "unknown"
        device_type = "unknown"

        if re_data.functionality_matrix.get("has_gpon"):
            device_type = "olt"
        elif re_data.functionality_matrix.get("has_interfaces"):
            device_type = "switch"

        # Try to determine vendor from OID patterns
        oids = list(re_data.discovered_oids.keys())
        if any("2011" in oid for oid in oids):
            vendor = "huawei"
        elif any("3902" in oid for oid in oids):
            vendor = "zte"
        elif any("39926" in oid for oid in oids):
            vendor = "vsol"

        return DeviceProfile(
            profile_id=f"re_{self.host}_{self.port}_{int(time.time())}",
            vendor=vendor,
            device_type=device_type,
            model="auto_discovered",
            contributed_by="reverse_engineering",
            working_oids=list(re_data.discovered_oids.keys()),
            data_mappings=re_data.data_mappings,
            tags=["auto-generated", "reverse-engineered"],
            metadata={
                "reverse_engineering_time": re_data.reverse_engineering_time,
                "success_rate": re_data.success_rate,
                "functionality_matrix": re_data.functionality_matrix
            }
        )

    def _determine_oids_to_collect(self) -> List[str]:
        """Determine which OIDs to collect based on available information."""
        oids = []

        # Prioritize from generated adapter
        if self.generated_adapter:
            oids.extend([mapping.oid for mapping in self.generated_adapter.oid_mappings])

        # Add from explored OIDs if no adapter
        if not oids and self.explored_oids:
            # Take a representative sample of explored OIDs
            accessible_oids = [oid for oid, node in self.explored_oids.items() if getattr(node, 'accessible', False)]
            oids.extend(accessible_oids[:50])  # Limit to top 50

        # Add standard OIDs if still empty
        if not oids:
            oids = [
                "1.3.6.1.2.1.1.1.0",  # System description
                "1.3.6.1.2.1.1.3.0",  # Uptime
                "1.3.6.1.2.1.1.5.0",  # System name
                "1.3.6.1.2.1.2.1.0",  # Interface count
            ]

        return list(set(oids))  # Remove duplicates

    async def _process_collected_data(
        self,
        collected_data: Dict[str, Any],
        strategy_results: List
    ) -> Dict[str, Any]:
        """Process collected data with intelligence enhancements."""
        processed_data = {}

        # Apply transforms if we have a generated adapter
        if self.generated_adapter and self.generated_adapter.transforms:
            processed_data = await self._apply_transforms(collected_data, self.generated_adapter.transforms)
        else:
            processed_data = collected_data.copy()

        # Add friendly name mappings
        if self.generated_adapter:
            for mapping in self.generated_adapter.oid_mappings:
                if mapping.oid in processed_data:
                    processed_data[mapping.name] = processed_data[mapping.oid]

        # Add intelligence annotations
        processed_data["_intelligence"] = {
            "collection_success_rate": len([r for r in strategy_results if r.success]) / len(strategy_results),
            "primary_method": strategy_results[0].method.value if strategy_results else "unknown",
            "data_sources": list(set(r.method.value for r in strategy_results if r.success))
        }

        return processed_data

    async def _apply_transforms(self, data: Dict[str, Any], transforms: List) -> Dict[str, Any]:
        """Apply transformation rules to collected data."""
        transformed_data = data.copy()

        for transform in transforms:
            if transform.input_pattern in transformed_data:
                try:
                    original_value = transformed_data[transform.input_pattern]

                    if transform.transformation_type == "scale":
                        scale_factor = transform.parameters.get("scale_factor", 1.0)
                        transformed_value = float(original_value) * scale_factor
                    elif transform.transformation_type == "format":
                        format_str = transform.parameters.get("format", "{value}")
                        transformed_value = format_str.format(value=original_value)
                    elif transform.transformation_type == "calculate":
                        # Simple calculations could be implemented here
                        transformed_value = original_value  # Placeholder
                    else:
                        transformed_value = original_value

                    transformed_data[transform.output_field] = transformed_value

                except Exception as e:
                    logger.warning(f"Transform {transform.name} failed: {e}")

        return transformed_data

    async def _learn_from_collection(self, collected_data: Dict[str, Any], strategy_results: List):
        """Learn from the collection results."""
        try:
            # Prepare learning data
            device_signature = {
                "vendor": self.signature.vendor.value if self.signature else "unknown",
                "device_type": self.signature.device_type.value if self.signature else "unknown",
                "model": self.signature.model if self.signature else "unknown"
            }

            discovered_oids = list(collected_data.keys())
            performance_metrics = {
                "response_time_ms": sum(r.execution_time_ms for r in strategy_results) / len(strategy_results),
                "success_rate": len([r for r in strategy_results if r.success]) / len(strategy_results)
            }

            # Create learning instance
            learning_instance_id = await self.self_learning.learn_from_device(
                device_id=f"{self.host}:{self.port}",
                device_signature=device_signature,
                discovered_oids=discovered_oids,
                collection_results=collected_data,
                performance_metrics=performance_metrics
            )

            self.learning_history.append(learning_instance_id)

            logger.debug(f"Created learning instance: {learning_instance_id}")

        except Exception as e:
            logger.error(f"Learning from collection failed: {e}")

    def _update_intelligent_metrics(self, data: Dict[str, Any], strategy_results: List, collection_time: float):
        """Update intelligent metrics."""
        # Update base metrics
        self.metrics.last_collection = datetime.now()
        self.metrics.response_time_ms = collection_time * 1000
        self.metrics.successful_collections += 1 if any(r.success for r in strategy_results) else 0

        # Update advanced metrics
        if not hasattr(self, 'intelligent_metrics'):
            self.intelligent_metrics = {
                "total_intelligent_collections": 0,
                "avg_discovery_improvement": 0.0,
                "strategy_success_rates": {},
                "learning_instances_count": 0
            }

        self.intelligent_metrics["total_intelligent_collections"] += 1
        self.intelligent_metrics["learning_instances_count"] = len(self.learning_history)

        # Track strategy success rates
        for result in strategy_results:
            method_name = result.method.value
            if method_name not in self.intelligent_metrics["strategy_success_rates"]:
                self.intelligent_metrics["strategy_success_rates"][method_name] = {
                    "successes": 0,
                    "total": 0
                }

            self.intelligent_metrics["strategy_success_rates"][method_name]["total"] += 1
            if result.success:
                self.intelligent_metrics["strategy_success_rates"][method_name]["successes"] += 1

    async def get_intelligent_insights(self) -> Dict[str, Any]:
        """Get comprehensive insights about the device."""
        insights = {
            "device_info": {
                "host": self.host,
                "port": self.port,
                "status": self.status.value,
                "signature": asdict(self.signature) if self.signature else None
            },
            "discovery_metrics": self.advanced_metrics,
            "learning_summary": {
                "total_learning_instances": len(self.learning_history),
                "recent_learning": self.learning_history[-5:] if self.learning_history else []
            },
            "collection_capabilities": {
                "oid_exploration_available": len(self.explored_oids) > 0,
                "reverse_engineered": self.reverse_engineered_data is not None,
                "profile_available": self.device_profile is not None,
                "adapter_generated": self.generated_adapter is not None
            },
            "performance_insights": getattr(self, 'intelligent_metrics', {}),
            "knowledge_base_matches": []
        }

        # Get similar devices from self-learning
        if self.signature:
            target_data = {
                "vendor": self.signature.vendor.value,
                "discovered_oids": list(self.explored_oids.keys())
            }

            similar_devices = await self.self_learning.find_similar_devices(target_data, max_results=5)
            insights["similar_devices"] = similar_devices

        # Get cluster insights if available
        if self.learning_history:
            clusters = await self.self_learning.get_device_clusters()
            for cluster in clusters.values():
                if f"{self.host}:{self.port}" in cluster.device_ids:
                    insights["cluster_insights"] = await self.self_learning.get_cluster_insights(cluster.cluster_id)
                    break

        return insights

    async def close(self):
        """Close enhanced device and cleanup all resources."""
        await super().close()

        # Close advanced components
        await self.oid_explorer.close()
        await self.reverse_engineer.close()
        await self.adapter_generator.close()
        await self.self_learning.close()
        await self.fallback_strategies.close()

        logger.info(f"Enhanced device {self.host} closed")