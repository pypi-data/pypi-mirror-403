"""
Adapter Generator - Dynamic adapter generation from device profiles.

This module automatically generates SNMP adapters from discovered device
profiles, learning patterns, and community contributions.
"""

import asyncio
import logging
import re
from typing import Dict, List, Set, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import time

from ..core.engine import SNMPEngine, SNMPTarget, SNMPResponse
from ..config.adapter import AdapterConfig, OIDMapping, TransformRule
from ..intelligence.knowledge_base import KnowledgeBase, DeviceProfile
from ..intelligence.oid_explorer import OIDNode, OIDNodeType
from ..intelligence.pattern_recognition import PatternMatcher

logger = logging.getLogger(__name__)


@dataclass
class GenerationTemplate:
    """Template for generating adapters."""
    template_id: str
    vendor: str
    device_type: str
    oid_patterns: Dict[str, List[str]] = field(default_factory=dict)
    transform_rules: List[Dict[str, Any]] = field(default_factory=list)
    collection_strategy: Dict[str, Any] = field(default_factory=dict)
    confidence_threshold: float = 0.6


class AdapterGenerator:
    """
    Dynamic adapter generator that creates adapters from device profiles.

    Features:
    - Generate adapters from discovered device profiles
    - Apply learned patterns from successful collections
    - Create vendor-specific optimization strategies
    - Validate generated adapters before deployment
    - Version and track adapter evolution
    """

    def __init__(self, knowledge_base: KnowledgeBase = None):
        """
        Initialize adapter generator.

        Args:
            knowledge_base: Knowledge base for device profiles
        """
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.pattern_recognition = PatternRecognition()
        self.snmp_engine = SNMPEngine()

        # Generation templates
        self.templates: Dict[str, GenerationTemplate] = {}
        self._load_builtin_templates()

        # Generated adapters
        self.generated_adapters: Dict[str, AdapterConfig] = {}

        # Statistics
        self.generation_stats = {
            "total_generated": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "active_adapters": 0,
            "last_generation": None
        }

    def _load_builtin_templates(self):
        """Load built-in generation templates."""
        # Huawei OLT template
        self.templates["huawei_olt"] = GenerationTemplate(
            template_id="huawei_olt",
            vendor="huawei",
            device_type="olt",
            oid_patterns={
                "system": [
                    "1.3.6.1.2.1.1.1.0",  # System description
                    "1.3.6.1.2.1.1.3.0",  # Uptime
                    "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.5",  # CPU
                    "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.7",  # Memory
                ],
                "gpon": [
                    "1.3.6.1.4.1.2011.6.128.1.1.1",  # Board info
                    "1.3.6.1.4.1.2011.6.128.1.1.3",  # ONT info
                    "1.3.6.1.4.1.2011.6.128.1.1.4",  # Optical info
                ]
            },
            transform_rules=[
                {
                    "name": "uptime_to_days",
                    "input_pattern": "system_uptime",
                    "output_field": "uptime_days",
                    "transformation_type": "scale",
                    "parameters": {"scale_factor": 0.000864}
                }
            ],
            collection_strategy={
                "use_bulk_walk": True,
                "max_repetitions": 20,
                "concurrent_requests": 10
            }
        )

        # ZTE OLT template
        self.templates["zte_olt"] = GenerationTemplate(
            template_id="zte_olt",
            vendor="zte",
            device_type="olt",
            oid_patterns={
                "system": [
                    "1.3.6.1.2.1.1.1.0",
                    "1.3.6.1.2.1.1.3.0",
                ],
                "gpon": [
                    "1.3.6.1.4.1.3902.110.1.1",  # Slot info
                    "1.3.6.1.4.1.3902.110.1.2",  # PON ports
                    "1.3.6.1.4.1.3902.110.1.3",  # ONU info
                ]
            },
            collection_strategy={
                "use_bulk_walk": True,
                "max_repetitions": 15,
                "concurrent_requests": 8
            }
        )

        # V-SOL OLT template (for undocumented devices)
        self.templates["vsol_olt"] = GenerationTemplate(
            template_id="vsol_olt",
            vendor="vsol",
            device_type="olt",
            oid_patterns={
                "system": [
                    "1.3.6.1.2.1.1.1.0",
                    "1.3.6.1.2.1.1.3.0",
                ],
                "gpon": [
                    "1.3.6.1.4.1.39926.1",  # System
                    "1.3.6.1.4.1.39926.2",  # Interfaces
                    "1.3.6.1.4.1.39926.3",  # GPON
                ]
            },
            collection_strategy={
                "use_bulk_walk": False,  # V-SOL might not support bulk operations
                "timeout": 10,  # Longer timeout for undocumented devices
                "retries": 5
            }
        )

    async def generate_adapter_from_profile(
        self,
        profile: DeviceProfile,
        validation_target: SNMPTarget = None
    ) -> AdapterConfig:
        """
        Generate an adapter from a device profile.

        Args:
            profile: Device profile to generate from
            validation_target: Optional target for validation

        Returns:
            Generated adapter configuration
        """
        logger.info(f"Generating adapter from profile: {profile.profile_id}")

        # Create adapter configuration
        adapter_config = AdapterConfig(
            name=f"auto_{profile.vendor}_{profile.device_type}_{profile.profile_id[:8]}",
            version="1.0.0",
            device_type=profile.device_type,
            vendor=profile.vendor,
            supported_models=[profile.model] if profile.model else [],
            oid_mappings=[],
            transforms=[],
            collection_strategy={}
        )

        # Generate OID mappings from profile
        await self._generate_oid_mappings(profile, adapter_config)

        # Generate transform rules
        await self._generate_transform_rules(profile, adapter_config)

        # Set collection strategy based on vendor patterns
        await self._set_collection_strategy(profile, adapter_config)

        # Validate adapter if target provided
        if validation_target:
            is_valid = await self._validate_adapter(adapter_config, validation_target)
            if is_valid:
                self.generation_stats["successful_validations"] += 1
            else:
                self.generation_stats["failed_validations"] += 1
                logger.warning(f"Generated adapter failed validation: {adapter_config.name}")

        # Store generated adapter
        self.generated_adapters[adapter_config.name] = adapter_config
        self.generation_stats["total_generated"] += 1
        self.generation_stats["last_generation"] = time.time()

        return adapter_config

    async def generate_adapter_from_discovery(
        self,
        vendor: str,
        device_type: str,
        discovered_oids: Dict[str, OIDNode],
        system_info: Dict[str, Any],
        validation_target: SNMPTarget = None
    ) -> AdapterConfig:
        """
        Generate an adapter from device discovery results.

        Args:
            vendor: Detected vendor
            device_type: Detected device type
            discovered_oids: Discovered OID tree
            system_info: System information
            validation_target: Optional target for validation

        Returns:
            Generated adapter configuration
        """
        logger.info(f"Generating adapter from discovery: {vendor} {device_type}")

        # Create temporary profile from discovery
        temp_profile = DeviceProfile(
            profile_id="discovery_temp",
            vendor=vendor,
            device_type=device_type,
            model=system_info.get("description", "Unknown"),
            working_oids=list(discovered_oids.keys()),
            tags=["auto-generated", "from-discovery"]
        )

        return await self.generate_adapter_from_profile(temp_profile, validation_target)

    async def improve_adapter(
        self,
        adapter_config: AdapterConfig,
        new_data: Dict[str, Any],
        feedback: Dict[str, Any] = None
    ) -> AdapterConfig:
        """
        Improve an existing adapter with new data.

        Args:
            adapter_config: Existing adapter to improve
            new_data: New discovered data
            feedback: Feedback on adapter performance

        Returns:
            Improved adapter configuration
        """
        logger.info(f"Improving adapter: {adapter_config.name}")

        # Clone the adapter
        improved_adapter = AdapterConfig(
            name=adapter_config.name,
            version=self._increment_version(adapter_config.version),
            device_type=adapter_config.device_type,
            vendor=adapter_config.vendor,
            supported_models=adapter_config.supported_models.copy(),
            oid_mappings=adapter_config.oid_mappings.copy(),
            transforms=adapter_config.transforms.copy(),
            collection_strategy=adapter_config.collection_strategy.copy()
        )

        # Add new OID mappings
        await self._add_new_oid_mappings(new_data, improved_adapter)

        # Optimize collection strategy based on feedback
        if feedback:
            await self._optimize_collection_strategy(improved_adapter, feedback)

        # Remove problematic OIDs based on feedback
        if feedback and feedback.get("problematic_oids"):
            await self._remove_problematic_oids(improved_adapter, feedback["problematic_oids"])

        return improved_adapter

    async def _generate_oid_mappings(self, profile: DeviceProfile, adapter_config: AdapterConfig):
        """Generate OID mappings from device profile."""
        # Get working OIDs from profile
        working_oids = profile.working_oids

        # Try to find a matching template
        template = self._find_matching_template(profile.vendor, profile.device_type)

        if template:
            # Use template to organize OIDs
            await self._apply_template_to_oids(template, working_oids, adapter_config)
        else:
            # Generic OID mapping
            await self._create_generic_oid_mappings(working_oids, adapter_config)

        # Add friendly name mappings from profile
        for friendly_name, oid in profile.oid_mappings.items():
            mapping = OIDMapping(
                name=friendly_name,
                oid=oid,
                description=f"Auto-mapped from profile: {profile.profile_id}",
                data_type="string",
                category="profile"
            )
            adapter_config.oid_mappings.append(mapping)

    async def _apply_template_to_oids(
        self,
        template: GenerationTemplate,
        working_oids: List[str],
        adapter_config: AdapterConfig
    ):
        """Apply a template to organize OIDs."""
        for category, pattern_oids in template.oid_patterns.items():
            # Find matching OIDs in working OIDs
            for pattern_oid in pattern_oids:
                # Exact match
                if pattern_oid in working_oids:
                    mapping = OIDMapping(
                        name=f"{category}_{self._oid_to_name(pattern_oid)}",
                        oid=pattern_oid,
                        description=f"Auto-generated from template {template.template_id}",
                        data_type="string",
                        category=category
                    )
                    adapter_config.oid_mappings.append(mapping)

                # Pattern match (for table branches)
                else:
                    matches = [oid for oid in working_oids if oid.startswith(pattern_oid)]
                    if matches:
                        for match in matches:
                            mapping = OIDMapping(
                                name=f"{category}_{self._oid_to_name(match)}",
                                oid=match,
                                description=f"Auto-generated from template {template.template_id}",
                                data_type="walk" if match != pattern_oid else "string",
                                category=category
                            )
                            adapter_config.oid_mappings.append(mapping)

    async def _create_generic_oid_mappings(
        self,
        working_oids: List[str],
        adapter_config: AdapterConfig
    ):
        """Create generic OID mappings when no template is available."""
        for oid in working_oids:
            name = self._oid_to_name(oid)
            category = self._categorize_oid(oid)

            mapping = OIDMapping(
                name=name,
                oid=oid,
                description="Auto-generated generic mapping",
                data_type="string",
                category=category
            )
            adapter_config.oid_mappings.append(mapping)

    async def _generate_transform_rules(self, profile: DeviceProfile, adapter_config: AdapterConfig):
        """Generate transform rules for the adapter."""
        # Add common transforms based on OID patterns

        # Uptime transformation
        uptime_mappings = [m for m in adapter_config.oid_mappings if "uptime" in m.name.lower()]
        for mapping in uptime_mappings:
            transform = TransformRule(
                name=f"{mapping.name}_to_days",
                input_pattern=mapping.name,
                output_field=f"{mapping.name}_days",
                transformation_type="scale",
                parameters={"scale_factor": 0.000864, "unit": "days"}
            )
            adapter_config.transforms.append(transform)

        # Memory transformations
        memory_mappings = [m for m in adapter_config.oid_mappings if "memory" in m.name.lower()]
        for mapping in memory_mappings:
            # KB to MB transformation
            transform = TransformRule(
                name=f"{mapping.name}_to_mb",
                input_pattern=mapping.name,
                output_field=f"{mapping.name}_mb",
                transformation_type="scale",
                parameters={"scale_factor": 0.001024, "unit": "MB"}
            )
            adapter_config.transforms.append(transform)

        # Percentage transformations
        percentage_mappings = [m for m in adapter_config.oid_mappings if any(
            keyword in m.name.lower() for keyword in ["usage", "utilization", "cpu"]
        )]
        for mapping in percentage_mappings:
            transform = TransformRule(
                name=f"{mapping.name}_percentage",
                input_pattern=mapping.name,
                output_field=f"{mapping.name}_percent",
                transformation_type="format",
                parameters={"format": "{value}%"}
            )
            adapter_config.transforms.append(transform)

        # Add transforms from profile if available
        for transform_data in profile.metadata.get("transforms", []):
            transform = TransformRule(
                name=transform_data["name"],
                input_pattern=transform_data["input_pattern"],
                output_field=transform_data["output_field"],
                transformation_type=transform_data["transformation_type"],
                parameters=transform_data.get("parameters", {})
            )
            adapter_config.transforms.append(transform)

    async def _set_collection_strategy(self, profile: DeviceProfile, adapter_config: AdapterConfig):
        """Set collection strategy based on vendor and device type."""
        # Default strategy
        default_strategy = {
            "use_bulk_walk": True,
            "max_repetitions": 20,
            "concurrent_requests": 10,
            "timeout": 5,
            "retries": 3
        }

        # Vendor-specific optimizations
        if profile.vendor.lower() == "vsol":
            # V-SOL devices might need conservative settings
            default_strategy.update({
                "use_bulk_walk": False,
                "timeout": 10,
                "retries": 5,
                "concurrent_requests": 5
            })
        elif profile.vendor.lower() == "huawei":
            # Huawei devices usually support advanced features
            default_strategy.update({
                "use_bulk_walk": True,
                "max_repetitions": 25,
                "concurrent_requests": 15
            })
        elif profile.vendor.lower() == "zte":
            # ZTE devices - moderate settings
            default_strategy.update({
                "use_bulk_walk": True,
                "max_repetitions": 15,
                "concurrent_requests": 8
            })

        # Use performance metrics from profile if available
        if profile.performance_metrics:
            avg_response_time = profile.performance_metrics.get("avg_response_time_ms", 50)
            if avg_response_time > 200:
                # Slow device - reduce concurrency
                default_strategy["concurrent_requests"] = max(3, default_strategy["concurrent_requests"] // 2)
                default_strategy["timeout"] = default_strategy["timeout"] * 2

        # Apply strategy from access patterns if available
        if profile.access_patterns:
            if profile.access_patterns.get("requires_v2c"):
                default_strategy["snmp_version"] = "v2c"
            if profile.access_patterns.get("max_oids_per_request"):
                default_strategy["max_repetitions"] = profile.access_patterns["max_oids_per_request"]

        adapter_config.collection_strategy = default_strategy

    async def _validate_adapter(
        self,
        adapter_config: AdapterConfig,
        target: SNMPTarget
    ) -> bool:
        """Validate an adapter configuration against a real device."""
        logger.info(f"Validating adapter: {adapter_config.name}")

        try:
            # Test a few key OIDs
            test_mappings = adapter_config.oid_mappings[:5]  # Test first 5 mappings

            success_count = 0
            for mapping in test_mappings:
                try:
                    response = await self.snmp_engine.get(target, [mapping.oid])
                    if response.success:
                        success_count += 1
                except Exception as e:
                    logger.debug(f"Validation failed for {mapping.oid}: {e}")

            success_rate = success_count / len(test_mappings) if test_mappings else 0
            logger.info(f"Adapter validation success rate: {success_rate:.2%}")

            return success_rate >= 0.6  # 60% success rate threshold

        except Exception as e:
            logger.error(f"Adapter validation failed: {e}")
            return False

    def _find_matching_template(self, vendor: str, device_type: str) -> Optional[GenerationTemplate]:
        """Find a matching template for vendor and device type."""
        template_key = f"{vendor.lower()}_{device_type.lower()}"
        return self.templates.get(template_key)

    def _oid_to_name(self, oid: str) -> str:
        """Convert OID to a readable name."""
        # Extract meaningful parts
        parts = oid.split('.')
        meaningful_parts = []

        # Look for significant numbers
        for part in parts[-4:]:  # Last 4 parts
            if part.isdigit() and int(part) < 1000:
                meaningful_parts.append(part)

        if meaningful_parts:
            return f"oid_{'_'.join(meaningful_parts)}"
        else:
            return f"oid_{parts[-1] if parts else 'unknown'}"

    def _categorize_oid(self, oid: str) -> str:
        """Categorize an OID based on its content."""
        oid_lower = oid.lower()

        if "1.3.6.1.2.1.1" in oid_lower:
            return "system"
        elif "1.3.6.1.2.1.2" in oid_lower:
            return "interfaces"
        elif any(keyword in oid_lower for keyword in ["gpon", "pon", "ont", "onu"]):
            return "gpon"
        elif any(keyword in oid_lower for keyword in ["cpu", "memory", "temp"]):
            return "performance"
        elif any(keyword in oid_lower for keyword in ["optic", "power", "signal"]):
            return "optical"
        else:
            return "general"

    def _increment_version(self, current_version: str) -> str:
        """Increment version number."""
        try:
            parts = current_version.split('.')
            if len(parts) >= 2:
                patch = int(parts[-1]) + 1
                return '.'.join(parts[:-1] + [str(patch)])
            else:
                return current_version + ".1"
        except ValueError:
            return current_version + ".1"

    async def _add_new_oid_mappings(self, new_data: Dict[str, Any], adapter_config: AdapterConfig):
        """Add new OID mappings from discovered data."""
        for friendly_name, oid in new_data.items():
            # Check if OID already exists
            existing = [m for m in adapter_config.oid_mappings if m.oid == oid]
            if not existing:
                mapping = OIDMapping(
                    name=friendly_name,
                    oid=oid,
                    description="Auto-added from improvement",
                    data_type="string",
                    category="improved"
                )
                adapter_config.oid_mappings.append(mapping)

    async def _optimize_collection_strategy(self, adapter_config: AdapterConfig, feedback: Dict[str, Any]):
        """Optimize collection strategy based on feedback."""
        avg_response_time = feedback.get("avg_response_time_ms", 50)
        error_rate = feedback.get("error_rate", 0.0)

        if avg_response_time > 200:
            # Slow responses - reduce concurrency
            adapter_config.collection_strategy["concurrent_requests"] = max(3, adapter_config.collection_strategy.get("concurrent_requests", 10) // 2)
            adapter_config.collection_strategy["timeout"] = adapter_config.collection_strategy.get("timeout", 5) * 2

        if error_rate > 0.1:
            # High error rate - increase retries and reduce bulk size
            adapter_config.collection_strategy["retries"] = min(10, adapter_config.collection_strategy.get("retries", 3) + 2)
            adapter_config.collection_strategy["max_repetitions"] = max(5, adapter_config.collection_strategy.get("max_repetitions", 20) - 5)

    async def _remove_problematic_oids(self, adapter_config: AdapterConfig, problematic_oids: List[str]):
        """Remove problematic OIDs from adapter."""
        original_count = len(adapter_config.oid_mappings)
        adapter_config.oid_mappings = [
            mapping for mapping in adapter_config.oid_mappings
            if mapping.oid not in problematic_oids
        ]
        removed_count = original_count - len(adapter_config.oid_mappings)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} problematic OIDs from adapter")

    def get_generated_adapter(self, adapter_name: str) -> Optional[AdapterConfig]:
        """Get a generated adapter by name."""
        return self.generated_adapters.get(adapter_name)

    def list_generated_adapters(self) -> List[str]:
        """List all generated adapter names."""
        return list(self.generated_adapters.keys())

    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get generation statistics."""
        self.generation_stats["active_adapters"] = len(self.generated_adapters)
        return self.generation_stats.copy()

    async def close(self):
        """Close adapter generator and cleanup resources."""
        await self.snmp_engine.close()