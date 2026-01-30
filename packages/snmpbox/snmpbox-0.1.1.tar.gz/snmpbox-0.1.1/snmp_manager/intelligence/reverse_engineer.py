"""
Reverse Engineer - Tools for discovering undocumented device capabilities.

This module specializes in reverse engineering undocumented devices,
particularly Chinese manufacturers like V-SOL, C-Data, and Fiberhome.
"""

import asyncio
import logging
import re
import time
from typing import Dict, List, Set, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from itertools import product
import hashlib

from ..core.engine import SNMPEngine, SNMPTarget, SNMPResponse
from .oid_explorer import OIDExplorer, OIDNode, OIDNodeType

logger = logging.getLogger(__name__)


@dataclass
class ReverseEngineeringResult:
    """Result of reverse engineering process."""
    device_id: str
    discovered_oids: Dict[str, OIDNode]
    data_mappings: Dict[str, str]  # Friendly name -> OID
    functionality_matrix: Dict[str, bool]  # Feature -> available
    confidence_scores: Dict[str, float]
    reverse_engineering_time: float
    success_rate: float


class OIDGuesser:
    """Intelligent OID guessing for undocumented devices."""

    def __init__(self):
        """Initialize OID guesser."""
        self.common_oid_patterns = {
            # System information patterns
            "system": [
                "1.3.6.1.2.1.1.1.0",    # Standard system desc
                "1.3.6.1.4.1.{enterprise}.1.1.0",     # Vendor system desc
                "1.3.6.1.4.1.{enterprise}.100.1.0",    # Alternative system desc
                "1.3.6.1.4.1.{enterprise}.1.0",       # Another variant
            ],

            # Device information patterns
            "device_info": [
                "1.3.6.1.4.1.{enterprise}.1.2.0",     # Device model
                "1.3.6.1.4.1.{enterprise}.1.3.0",     # Firmware version
                "1.3.6.1.4.1.{enterprise}.1.4.0",     # Serial number
                "1.3.6.1.4.1.{enterprise}.1.5.0",     # MAC address
            ],

            # Performance monitoring patterns
            "performance": [
                "1.3.6.1.4.1.{enterprise}.10.1.0",    # CPU usage
                "1.3.6.1.4.1.{enterprise}.10.2.0",    # Memory usage
                "1.3.6.1.4.1.{enterprise}.10.3.0",    # Temperature
                "1.3.6.1.4.1.{enterprise}.20.1.0",    # Uptime
            ],

            # GPON-specific patterns
            "gpon": [
                "1.3.6.1.4.1.{enterprise}.100.1.1",    # GPON board info
                "1.3.6.1.4.1.{enterprise}.100.1.2",    # PON ports
                "1.3.6.1.4.1.{enterprise}.100.1.3",    # ONT/ONU info
                "1.3.6.1.4.1.{enterprise}.100.1.4",    # Optical monitoring
                "1.3.6.1.4.1.{enterprise}.200.1.1",    # Alternative GPON
                "1.3.6.1.4.1.{enterprise}.200.1.2",    # Alternative ONT
            ],

            # Interface patterns
            "interfaces": [
                "1.3.6.1.4.1.{enterprise}.50.1.1",     # Interface status
                "1.3.6.1.4.1.{enterprise}.50.1.2",     # Interface statistics
                "1.3.6.1.4.1.{enterprise}.50.2.1",     # Port configuration
            ]
        }

        # Known enterprise IDs for common manufacturers
        self.enterprise_ids = {
            "vsol": "39926",
            "cdata": "99999",  # Example, needs real value
            "fiberhome": "86",
            "bdcom": "45018",
            "coretek": "46209",
            "cdata_com": "48390",
        }

    def generate_oid_candidates(
        self,
        vendor: str,
        category: str,
        max_variants: int = 20
    ) -> List[str]:
        """
        Generate candidate OIDs for a vendor and category.

        Args:
            vendor: Vendor name
            category: Category of OIDs (system, gpon, etc.)
            max_variants: Maximum number of variants to generate

        Returns:
            List of candidate OIDs
        """
        candidates = []

        # Get enterprise ID
        enterprise_id = self.enterprise_ids.get(vendor.lower())
        if not enterprise_id:
            # Try to guess from known patterns
            enterprise_id = "99999"  # Generic

        patterns = self.common_oid_patterns.get(category, [])

        for pattern in patterns:
            # Substitute enterprise ID
            oid = pattern.replace("{enterprise}", enterprise_id)
            candidates.append(oid)

            # Generate variants
            base_pattern = oid.rsplit('.', 1)[0]  # Remove last part

            # Common suffixes to try
            suffixes = ["0", "1", "2", "10", "100", "1.0", "2.0"]
            for suffix in suffixes[:max_variants // len(patterns)]:
                variant = f"{base_pattern}.{suffix}"
                candidates.append(variant)

        return candidates[:max_variants]

    def generate_sequential_oids(
        self,
        base_oid: str,
        count: int = 20,
        step: int = 1
    ) -> List[str]:
        """Generate sequential OIDs for exploration."""
        base_parts = base_oid.split('.')
        oids = []

        for i in range(count):
            new_parts = base_parts.copy()
            new_parts[-1] = str(int(new_parts[-1]) + (i * step))
            oids.append('.'.join(new_parts))

        return oids


class DataAnalyzer:
    """Analyzes SNMP data to infer meaning and structure."""

    def __init__(self):
        """Initialize data analyzer."""
        self.value_patterns = {
            "temperature": [
                r"^\d{1,3}\.\d$|^\d{1,2}$",  # 42.5 or 42
                r"^-?\d{1,3}\.?\d*C?$",     # May have C suffix
            ],
            "percentage": [
                r"^\d{1,3}%$|^\d{1,3}$",     # 85% or 85
                r"^0?\.\d+$|^[01]\.\d+$",   # 0.85 or 1.0
            ],
            "mac_address": [
                r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$",
                r"^([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}$",
                r"^[0-9A-Fa-f]{12}$",
            ],
            "ip_address": [
                r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
            ],
            "uptime": [
                r"^\d+$",                    # Timeticks
                r"^\d+ days?, \d+:\d+:\d+\.\d+",  # Human readable
            ],
            "serial_number": [
                r"^[A-Z0-9]{8,}$",          # Alphanumeric serials
                r"^[A-Z]{2}\d{6,}$",         # Letter + number pattern
            ]
        }

    def classify_value(self, value: str, oid: str) -> Dict[str, Any]:
        """
        Classify the type and meaning of an SNMP value.

        Args:
            value: SNMP value string
            oid: OID that produced the value

        Returns:
            Classification result with confidence
        """
        if not value or value in ["No Such Object available", "No Such Instance", "endOfMibView"]:
            return {"type": "error", "confidence": 1.0}

        classifications = []

        # Check against patterns
        for data_type, patterns in self.value_patterns.items():
            for pattern in patterns:
                if re.match(pattern, value):
                    confidence = self._calculate_pattern_confidence(value, pattern, data_type)
                    classifications.append((data_type, confidence))

        # Check OID context clues
        context_hints = self._analyze_oid_context(oid, value)
        classifications.extend(context_hints)

        # Select best classification
        if classifications:
            best_type, best_confidence = max(classifications, key=lambda x: x[1])
            return {
                "type": best_type,
                "confidence": best_confidence,
                "raw_value": value,
                "all_classifications": classifications
            }

        return {
            "type": "string",
            "confidence": 0.5,
            "raw_value": value,
            "all_classifications": []
        }

    def _calculate_pattern_confidence(self, value: str, pattern: str, data_type: str) -> float:
        """Calculate confidence score for a pattern match."""
        base_confidence = 0.7

        # Adjust confidence based on data type and value characteristics
        if data_type == "temperature":
            try:
                temp_val = float(re.sub(r'[^0-9.-]', '', value))
                if 0 <= temp_val <= 100:  # Reasonable temperature range
                    base_confidence = 0.9
                elif -20 <= temp_val <= 150:  # Extended range
                    base_confidence = 0.8
            except ValueError:
                pass

        elif data_type == "percentage":
            try:
                pct_val = float(re.sub(r'[^0-9.]', '', value))
                if 0 <= pct_val <= 100:  # Valid percentage range
                    base_confidence = 0.9
            except ValueError:
                pass

        elif data_type == "mac_address":
            if re.match(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$", value):
                base_confidence = 0.95  # Standard format

        elif data_type == "ip_address":
            parts = value.split('.')
            if len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts):
                base_confidence = 0.95  # Valid IP

        return base_confidence

    def _analyze_oid_context(self, oid: str, value: str) -> List[Tuple[str, float]]:
        """Analyze OID context for type hints."""
        hints = []

        oid_lower = oid.lower()

        # Temperature indicators
        if any(keyword in oid_lower for keyword in ["temp", "thermal", "heat", "celsius"]):
            hints.append(("temperature", 0.8))

        # CPU indicators
        if any(keyword in oid_lower for keyword in ["cpu", "processor", "utilization"]):
            hints.append(("percentage", 0.7))

        # Memory indicators
        if any(keyword in oid_lower for keyword in ["memory", "ram", "mem"]):
            try:
                mem_val = int(value)
                if mem_val > 1000:  # Likely KB or MB
                    hints.append(("memory_size", 0.8))
                else:  # Likely percentage
                    hints.append(("percentage", 0.7))
            except ValueError:
                pass

        # Uptime indicators
        if any(keyword in oid_lower for keyword in ["uptime", "sysuptime", "boot"]):
            hints.append(("uptime", 0.9))

        # Interface indicators
        if any(keyword in oid_lower for keyword in ["interface", "port", "if"]):
            hints.append(("interface_metric", 0.7))

        # Optical indicators
        if any(keyword in oid_lower for keyword in ["optic", "optical", "power", "signal", "loss"]):
            hints.append(("optical_metric", 0.8))

        return hints

    def infer_table_structure(self, oid_responses: Dict[str, str]) -> Dict[str, Any]:
        """
        Infer table structure from multiple OID responses.

        Args:
            oid_responses: Mapping of OIDs to their values

        Returns:
            Inferred table structure
        """
        structure = {
            "tables": [],
            "relationships": [],
            "key_fields": []
        }

        # Group OIDs by common prefixes
        oid_groups = defaultdict(list)
        for oid in oid_responses.keys():
            prefix = '.'.join(oid.split('.')[:-1])  # Remove last part
            oid_groups[prefix].append(oid)

        # Analyze each group as potential table
        for prefix, oids in oid_groups.items():
            if len(oids) > 2:  # Likely a table
                table_info = {
                    "base_oid": prefix,
                    "columns": [],
                    "estimated_rows": len(oids),
                    "sample_data": {}
                }

                # Analyze column types
                for oid in oids[:5]:  # Sample first 5
                    value = oid_responses[oid]
                    classification = self.classify_value(value, oid)
                    column_name = oid.split('.')[-1]

                    table_info["columns"].append({
                        "oid": oid,
                        "name": column_name,
                        "type": classification["type"],
                        "confidence": classification["confidence"]
                    })

                    table_info["sample_data"][column_name] = value

                structure["tables"].append(table_info)

        return structure


class ReverseEngineer:
    """
    Main reverse engineering class for undocumented devices.

    Features:
    - Intelligent OID guessing and probing
    - Data pattern analysis and classification
    - Table structure inference
    - Functionality matrix generation
    - Progressive learning from device responses
    """

    def __init__(self, snmp_engine: SNMPEngine = None):
        """
        Initialize reverse engineer.

        Args:
            snmp_engine: SNMP engine to use for operations
        """
        self.snmp_engine = snmp_engine or SNMPEngine()
        self.oid_guesser = OIDGuesser()
        self.data_analyzer = DataAnalyzer()
        self.learning_cache: Dict[str, Any] = {}

    async def reverse_engineer_device(
        self,
        target: SNMPTarget,
        vendor_hint: str = None,
        max_time_seconds: int = 300
    ) -> ReverseEngineeringResult:
        """
        Perform comprehensive reverse engineering of a device.

        Args:
            target: SNMP target to reverse engineer
            vendor_hint: Optional vendor hint
            max_time_seconds: Maximum time to spend

        Returns:
            Reverse engineering result
        """
        device_id = f"{target.host}:{target.port}"
        start_time = time.time()

        logger.info(f"Starting reverse engineering for {device_id}")

        discovered_oids = {}
        data_mappings = {}
        functionality_matrix = defaultdict(bool)
        confidence_scores = defaultdict(float)

        # Phase 1: Quick discovery using standard patterns
        logger.info("Phase 1: Standard pattern discovery")
        await self._discover_standard_oids(target, discovered_oids)

        # Phase 2: Vendor-specific pattern discovery
        if vendor_hint:
            logger.info(f"Phase 2: Vendor-specific discovery for {vendor_hint}")
            await self._discover_vendor_oids(target, vendor_hint, discovered_oids)

        # Phase 3: Brute-force exploration
        logger.info("Phase 3: Brute-force OID exploration")
        await self._brute_force_exploration(target, discovered_oids, max_time_seconds)

        # Phase 4: Data analysis and classification
        logger.info("Phase 4: Data analysis and classification")
        await self._analyze_discovered_data(discovered_oids, data_mappings, functionality_matrix)

        # Phase 5: Confidence scoring
        await self._calculate_confidence_scores(discovered_oids, confidence_scores)

        end_time = time.time()
        total_time = end_time - start_time

        # Calculate success rate
        attempted_oids = len(discovered_oids)
        successful_oids = len([n for n in discovered_oids.values() if n.accessible])
        success_rate = successful_oids / attempted_oids if attempted_oids > 0 else 0

        result = ReverseEngineeringResult(
            device_id=device_id,
            discovered_oids=discovered_oids,
            data_mappings=data_mappings,
            functionality_matrix=dict(functionality_matrix),
            confidence_scores=dict(confidence_scores),
            reverse_engineering_time=total_time,
            success_rate=success_rate
        )

        logger.info(f"Reverse engineering completed for {device_id}: "
                   f"{len(discovered_oids)} OIDs, {success_rate:.2%} success rate")

        return result

    async def _discover_standard_oids(self, target: SNMPTarget, discovered_oids: Dict[str, OIDNode]):
        """Discover standard OIDs using known patterns."""
        standard_oids = [
            # System
            "1.3.6.1.2.1.1.1.0",      # System description
            "1.3.6.1.2.1.1.3.0",      # Uptime
            "1.3.6.1.2.1.1.5.0",      # System name
            "1.3.6.1.2.1.1.6.0",      # Location

            # Interfaces
            "1.3.6.1.2.1.2.1.0",      # Interface count
            "1.3.6.1.2.1.2.2.1.2",    # Interface descriptions

            # Enterprise
            "1.3.6.1.4.1.1",          # Some devices start here
            "1.3.6.1.4.1.9",          # Cisco-like
            "1.3.6.1.4.1.2011",       # Huawei-like
            "1.3.6.1.4.1.3902",       # ZTE-like
            "1.3.6.1.4.1.39926",      # V-SOL-like
        ]

        for oid in standard_oids:
            node = await self._probe_oid_safe(target, oid)
            if node:
                discovered_oids[oid] = node

        # Try walking standard branches
        branches_to_walk = ["1.3.6.1.2.1.1", "1.3.6.1.2.1.2"]
        for branch in branches_to_walk:
            await self._walk_branch_safe(target, branch, discovered_oids, max_depth=3)

    async def _discover_vendor_oids(
        self,
        target: SNMPTarget,
        vendor: str,
        discovered_oids: Dict[str, OIDNode]
    ):
        """Discover vendor-specific OIDs."""
        categories = ["system", "device_info", "performance", "gpon", "interfaces"]

        for category in categories:
            candidates = self.oid_guesser.generate_oid_candidates(vendor, category)
            logger.debug(f"Testing {len(candidates)} {category} candidates for {vendor}")

            for oid in candidates:
                node = await self._probe_oid_safe(target, oid)
                if node:
                    discovered_oids[oid] = node
                    logger.debug(f"Discovered {category} OID: {oid}")

                    # If we found something in this category, explore nearby
                    await self._explore_nearby_oids(target, oid, discovered_oids, count=5)

    async def _brute_force_exploration(
        self,
        target: SNMPTarget,
        discovered_oids: Dict[str, OIDNode],
        max_time_seconds: int
    ):
        """Perform brute-force OID exploration."""
        start_time = time.time()

        # Start with known enterprise IDs
        enterprise_seeds = ["2011", "3902", "39926", "86", "9", "2636"]  # Huawei, ZTE, V-SOL, Fiberhome, Cisco, Juniper

        for enterprise_id in enterprise_seeds:
            if time.time() - start_time > max_time_seconds * 0.8:  # Leave 20% time for analysis
                break

            base_oid = f"1.3.6.1.4.1.{enterprise_id}"

            # Try common branch numbers
            branch_numbers = [1, 2, 10, 100, 1000, 2, 20, 200]

            for branch_num in branch_numbers:
                if time.time() - start_time > max_time_seconds * 0.8:
                    break

                branch_oid = f"{base_oid}.{branch_num}"
                node = await self._probe_oid_safe(target, branch_oid)

                if node:
                    discovered_oids[branch_oid] = node
                    logger.debug(f"Brute-force discovered: {branch_oid}")

                    # Explore this branch
                    await self._explore_branch(target, branch_oid, discovered_oids, depth=3)

    async def _explore_nearby_oids(
        self,
        target: SNMPTarget,
        base_oid: str,
        discovered_oids: Dict[str, OIDNode],
        count: int = 10
    ):
        """Explore OIDs near a discovered OID."""
        base_parts = base_oid.split('.')

        # Generate nearby OIDs by varying the last few parts
        for i in range(count):
            new_parts = base_parts.copy()
            new_parts[-1] = str(int(new_parts[-1]) + i + 1)
            nearby_oid = '.'.join(new_parts)

            node = await self._probe_oid_safe(target, nearby_oid)
            if node:
                discovered_oids[nearby_oid] = node

    async def _explore_branch(
        self,
        target: SNMPTarget,
        base_oid: str,
        discovered_oids: Dict[str, OIDNode],
        depth: int = 3
    ):
        """Explore a branch of OIDs."""
        if depth <= 0:
            return

        # Try sub-branches
        for i in range(1, 10):  # Try numbers 1-9
            sub_oid = f"{base_oid}.{i}"
            node = await self._probe_oid_safe(target, sub_oid)

            if node:
                discovered_oids[sub_oid] = node

                # Recursively explore deeper
                if node.node_type in [OIDNodeType.BRANCH, OIDNodeType.TABLE_ENTRY]:
                    await self._explore_branch(target, sub_oid, discovered_oids, depth - 1)

    async def _analyze_discovered_data(
        self,
        discovered_oids: Dict[str, OIDNode],
        data_mappings: Dict[str, str],
        functionality_matrix: Dict[str, bool]
    ):
        """Analyze discovered data to create mappings and functionality matrix."""
        # Collect values for analysis
        oid_values = {}
        for oid, node in discovered_oids.items():
            if node.accessible and hasattr(node, 'value') and node.value:
                oid_values[oid] = node.value

        # Classify each value and create friendly mappings
        for oid, value in oid_values.items():
            classification = self.data_analyzer.classify_value(value, oid)

            # Generate friendly name
            friendly_name = self._generate_friendly_name(oid, classification)
            data_mappings[friendly_name] = oid

        # Build functionality matrix
        functionality_matrix["has_system_info"] = any(
            "system" in oid.lower() or "1.3.6.1.2.1.1" in oid
            for oid in discovered_oids.keys()
        )

        functionality_matrix["has_interfaces"] = any(
            "interface" in oid.lower() or "1.3.6.1.2.1.2" in oid
            for oid in discovered_oids.keys()
        )

        functionality_matrix["has_gpon"] = any(
            "gpon" in oid.lower() or "6.128" in oid or "110" in oid
            for oid in discovered_oids.keys()
        )

        functionality_matrix["has_performance_monitoring"] = any(
            classification["type"] in ["temperature", "percentage"]
            for classification in [
                self.data_analyzer.classify_value(
                    next((n.value for n in discovered_oids.values()
                         if hasattr(n, 'value') and n.oid == oid), ""), oid
                )
                for oid in discovered_oids.keys()
            ]
            if hasattr(next(iter(discovered_oids.values())), 'value')
        )

    def _generate_friendly_name(self, oid: str, classification: Dict[str, Any]) -> str:
        """Generate a friendly name for an OID."""
        oid_parts = oid.split('.')
        data_type = classification.get("type", "unknown")

        # Extract meaningful parts of OID
        meaningful_parts = []
        for part in oid_parts[-4:]:  # Last 4 parts are usually most meaningful
            if part.isdigit() and int(part) < 10000:  # Skip large numbers
                meaningful_parts.append(part)

        # Name based on data type and OID context
        if data_type == "temperature":
            return f"temperature_celsius_{'. '.join(meaningful_parts[-2:])}"
        elif data_type == "percentage":
            if "cpu" in oid.lower():
                return "cpu_usage_percent"
            elif "memory" in oid.lower():
                return "memory_usage_percent"
            else:
                return f"usage_percent_{'. '.join(meaningful_parts[-2:])}"
        elif data_type == "uptime":
            return "system_uptime"
        elif data_type == "mac_address":
            return "device_mac_address"
        elif data_type == "ip_address":
            return "device_ip_address"
        else:
            return f"{data_type}_{'. '.join(meaningful_parts[-2:])}"

    async def _calculate_confidence_scores(
        self,
        discovered_oids: Dict[str, OIDNode],
        confidence_scores: Dict[str, float]
    ):
        """Calculate confidence scores for discoveries."""
        total_oids = len(discovered_oids)
        accessible_oids = len([n for n in discovered_oids.values() if n.accessible])

        if total_oids > 0:
            confidence_scores["discovery_quality"] = accessible_oids / total_oids
            confidence_scores["coverage"] = min(total_oids / 100, 1.0)  # Assume 100 OIDs is good coverage
        else:
            confidence_scores["discovery_quality"] = 0.0
            confidence_scores["coverage"] = 0.0

        # Vendor-specific confidence
        enterprise_oids = [oid for oid in discovered_oids.keys() if "4.1." in oid]
        confidence_scores["vendor_specific_coverage"] = len(enterprise_oids) / max(total_oids, 1)

    async def _probe_oid_safe(self, target: SNMPTarget, oid: str) -> Optional[OIDNode]:
        """Safely probe an OID with error handling."""
        try:
            response = await self.snmp_engine.get(target, [oid])
            if response.success and response.var_binds:
                value = response.var_binds[0][1] if response.var_binds else None

                # Classify the value
                classification = self.data_analyzer.classify_value(value, oid)

                return OIDNode(
                    oid=oid,
                    accessible=True,
                    node_type=OIDNodeType.SCALAR,
                    value_type=classification["type"],
                    confidence=classification["confidence"]
                )
        except Exception as e:
            logger.debug(f"Failed to probe OID {oid}: {e}")

        return None

    async def _walk_branch_safe(
        self,
        target: SNMPTarget,
        branch_oid: str,
        discovered_oids: Dict[str, OIDNode],
        max_depth: int = 3
    ):
        """Safely walk a branch with error handling."""
        try:
            response = await self.snmp_engine.walk(target, branch_oid, max_repetitions=10)
            if response.success and response.var_binds:
                for oid_str, value in response.var_binds:
                    if oid_str not in discovered_oids:
                        classification = self.data_analyzer.classify_value(value, oid_str)
                        node = OIDNode(
                            oid=oid_str,
                            accessible=True,
                            node_type=OIDNodeType.LEAF,
                            value_type=classification["type"],
                            confidence=classification["confidence"]
                        )
                        discovered_oids[oid_str] = node
        except Exception as e:
            logger.debug(f"Failed to walk branch {branch_oid}: {e}")

    async def close(self):
        """Close reverse engineer and cleanup resources."""
        await self.snmp_engine.close()
        self.learning_cache.clear()