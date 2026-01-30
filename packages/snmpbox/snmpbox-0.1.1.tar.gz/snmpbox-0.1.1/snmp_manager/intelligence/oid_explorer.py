"""
OID Explorer - Intelligent discovery and mapping of device OID trees.

This module implements adaptive tree walking algorithms to discover
and map unknown device OIDs, especially for undocumented devices.
"""

import asyncio
import logging
import re
from typing import Dict, List, Set, Optional, Tuple, Any, NamedTuple
from dataclasses import dataclass
from enum import Enum
import time
from collections import defaultdict, deque

from ..core.engine import SNMPEngine, SNMPTarget, SNMPResponse

logger = logging.getLogger(__name__)


class OIDNodeType(Enum):
    """Types of OID nodes discovered during exploration."""
    UNKNOWN = "unknown"
    SCALAR = "scalar"          # Single value OID
    TABLE_ENTRY = "table"       # Table entry (can be walked)
    BRANCH = "branch"          # Tree branch
    LEAF = "leaf"              # Tree leaf
    END_OF_MIB = "eom"         # End of MIB view
    ERROR = "error"            # Error response


@dataclass
class OIDNode:
    """Represents a discovered OID node."""
    oid: str
    name: Optional[str] = None
    description: Optional[str] = None
    node_type: OIDNodeType = OIDNodeType.UNKNOWN
    value_type: Optional[str] = None
    accessible: bool = False
    children: List[str] = None
    parent: Optional[str] = None
    confidence: float = 0.0
    vendor_hints: List[str] = None
    last_accessed: Optional[float] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.vendor_hints is None:
            self.vendor_hints = []


@dataclass
class ExplorationStrategy:
    """Strategy for OID exploration."""
    name: str
    priority: int
    max_depth: int
    batch_size: int
    timeout: float
    retry_count: int
    skip_patterns: List[str] = None
    focus_patterns: List[str] = None

    def __post_init__(self):
        if self.skip_patterns is None:
            self.skip_patterns = []
        if self.focus_patterns is None:
            self.focus_patterns = []


class OIDExplorer:
    """
    Intelligent OID tree explorer for discovering unknown device capabilities.

    Features:
    - Adaptive tree walking with multiple strategies
    - Pattern-based OID classification
    - Vendor-specific hint detection
    - Performance optimization with caching
    - Error handling and recovery
    - Incremental exploration and learning
    """

    def __init__(self, snmp_engine: SNMPEngine = None):
        """
        Initialize OID Explorer.

        Args:
            snmp_engine: SNMP engine to use for operations
        """
        self.snmp_engine = snmp_engine or SNMPEngine()
        self.discovered_trees: Dict[str, Dict[str, OIDNode]] = {}
        self.exploration_cache: Dict[str, Any] = {}
        self.exploration_stats: Dict[str, Any] = defaultdict(int)

        # Known OID patterns for different vendors
        self.vendor_patterns = {
            "huawei": {
                "prefixes": ["1.3.6.1.4.1.2011"],
                "common_branches": [
                    "1.3.6.1.4.1.2011.6.128",  # GPON
                    "1.3.6.1.4.1.2011.5.25",   # Device management
                    "1.3.6.1.4.1.2011.5",      # Huawei enterprise
                ],
                "patterns": [
                    r"1\.3\.6\.1\.4\.1\.2011\.6\.128\.\d+\.1\.\d+",  # GPON board
                    r"1\.3\.6\.1\.4\.1\.2011\.5\.25\.\d+\.\d+",     # Device info
                ]
            },
            "zte": {
                "prefixes": ["1.3.6.1.4.1.3902"],
                "common_branches": [
                    "1.3.6.1.4.1.3902.110",   # ZTE GPON
                    "1.3.6.1.4.1.3902.1",     # ZTE system
                ],
                "patterns": [
                    r"1\.3\.6\.1\.4\.1\.3902\.110\.\d+\.\d+",      # GPON slots
                ]
            },
            "vsol": {
                "prefixes": ["1.3.6.1.4.1.39926"],
                "common_branches": [
                    "1.3.6.1.4.1.39926.1",    # System
                    "1.3.6.1.4.1.39926.2",    # Interfaces
                    "1.3.6.1.4.1.39926.3",    # GPON
                ],
                "patterns": [
                    r"1\.3\.6\.1\.4\.1\.39926\.\d+\.\d+",          # V-SOL structure
                ]
            }
        }

        # Common OID patterns to always explore
        self.universal_branches = [
            "1.3.6.1.2.1.1",      # System group
            "1.3.6.1.2.1.2",      # Interfaces
            "1.3.6.1.2.1.4",      # IP
            "1.3.6.1.2.1.31",     # Interface extensions
            "1.3.6.1.4.1",        # Enterprise
        ]

        # Exploration strategies
        self.strategies = [
            ExplorationStrategy(
                name="standard",
                priority=1,
                max_depth=10,
                batch_size=20,
                timeout=2.0,
                retry_count=2,
                focus_patterns=[r"1\.3\.6\.1\.4\.1\.(\d+)"]
            ),
            ExplorationStrategy(
                name="deep_dive",
                priority=2,
                max_depth=20,
                batch_size=10,
                timeout=3.0,
                retry_count=3,
                skip_patterns=[r"\.255\.255$", r"\.0\.0$"]  # Skip end-of-mib markers
            ),
            ExplorationStrategy(
                name="vendor_specific",
                priority=3,
                max_depth=15,
                batch_size=15,
                timeout=2.5,
                retry_count=2,
                focus_patterns=[r"1\.3\.6\.1\.4\.1\.2011", r"1\.3\.6\.1\.4\.1\.3902"]
            )
        ]

    async def explore_device(
        self,
        target: SNMPTarget,
        strategies: List[ExplorationStrategy] = None
    ) -> Dict[str, OIDNode]:
        """
        Explore device OID tree and build map.

        Args:
            target: SNMP target to explore
            strategies: Exploration strategies to use

        Returns:
            Dictionary of discovered OID nodes
        """
        device_key = f"{target.host}:{target.port}"
        logger.info(f"Starting OID exploration for {device_key}")

        if strategies is None:
            strategies = self.strategies

        # Initialize exploration tree
        oid_tree = {}

        # Start with known good OIDs
        await self._explore_known_branches(target, oid_tree)

        # Apply exploration strategies
        for strategy in sorted(strategies, key=lambda s: s.priority):
            logger.info(f"Applying strategy: {strategy.name}")
            await self._apply_strategy(target, strategy, oid_tree)

        # Post-process and classify discovered nodes
        await self._classify_nodes(target, oid_tree)

        # Store results
        self.discovered_trees[device_key] = oid_tree
        self.exploration_stats[f"{device_key}_nodes"] = len(oid_tree)
        self.exploration_stats[f"{device_key}_timestamp"] = time.time()

        logger.info(f"Exploration completed for {device_key}: {len(oid_tree)} nodes discovered")
        return oid_tree

    async def _explore_known_branches(self, target: SNMPTarget, oid_tree: Dict[str, OIDNode]):
        """Explore known OID branches that are likely to be accessible."""
        logger.debug("Exploring known OID branches")

        # Test universal branches
        for base_oid in self.universal_branches:
            try:
                response = await self.snmp_engine.get(target, [base_oid])
                if response.success:
                    node = OIDNode(
                        oid=base_oid,
                        accessible=True,
                        node_type=OIDNodeType.BRANCH,
                        confidence=0.9
                    )
                    oid_tree[base_oid] = node

                    # Try to walk this branch
                    await self._walk_branch(target, base_oid, oid_tree, max_depth=5)

            except Exception as e:
                logger.debug(f"Failed to explore {base_oid}: {e}")

    async def _apply_strategy(
        self,
        target: SNMPTarget,
        strategy: ExplorationStrategy,
        oid_tree: Dict[str, OIDNode]
    ):
        """Apply a specific exploration strategy."""
        logger.debug(f"Applying strategy: {strategy.name}")

        # Generate OIDs to explore based on strategy
        exploration_queue = deque()

        # Add focus patterns
        for pattern in strategy.focus_patterns:
            base_oids = self._generate_oid_patterns(pattern)
            exploration_queue.extend(base_oids)

        # Add vendor-specific branches if any vendor hints exist
        vendor_hints = self._detect_vendor_from_tree(oid_tree)
        for vendor in vendor_hints:
            if vendor in self.vendor_patterns:
                vendor_branches = self.vendor_patterns[vendor]["common_branches"]
                exploration_queue.extend(vendor_branches)

        # Explore the queue
        while exploration_queue and len(oid_tree) < 1000:  # Limit total nodes
            current_oid = exploration_queue.popleft()

            if current_oid in oid_tree:
                continue  # Already explored

            # Skip if matches skip patterns
            if any(re.search(pattern, current_oid) for pattern in strategy.skip_patterns):
                continue

            # Try to access this OID
            try:
                node = await self._probe_oid(target, current_oid, strategy)
                if node:
                    oid_tree[current_oid] = node

                    # If accessible and looks like a branch, explore children
                    if node.accessible and node.node_type in [OIDNodeType.BRANCH, OIDNodeType.TABLE_ENTRY]:
                        children = await self._discover_children(target, current_oid, strategy)
                        exploration_queue.extend(children)

            except Exception as e:
                logger.debug(f"Failed to probe {current_oid}: {e}")

    async def _probe_oid(
        self,
        target: SNMPTarget,
        oid: str,
        strategy: ExplorationStrategy
    ) -> Optional[OIDNode]:
        """Probe a specific OID and classify it."""
        try:
            # Try GET first
            get_response = await self.snmp_engine.get(target, [oid])

            if get_response.success and get_response.var_binds:
                value = get_response.var_binds[0][1] if get_response.var_binds else None
                node = OIDNode(
                    oid=oid,
                    accessible=True,
                    node_type=OIDNodeType.SCALAR,
                    value_type=self._classify_value_type(value),
                    confidence=0.8,
                    last_accessed=time.time()
                )
                return node

            # If GET fails, try GETNEXT to see if it's a walkable branch
            next_response = await self.snmp_engine.get_next(target, [oid])

            if next_response.success and next_response.var_binds:
                next_oid = next_response.var_binds[0][0]

                # Check if we got a different OID (indicating it's walkable)
                if next_oid != oid:
                    node = OIDNode(
                        oid=oid,
                        accessible=True,
                        node_type=OIDNodeType.BRANCH,
                        confidence=0.7,
                        last_accessed=time.time()
                    )
                    return node

            # Try WALK for table-like structures
            walk_response = await self.snmp_engine.walk(target, oid, max_repetitions=5)

            if walk_response.success and walk_response.var_binds:
                node = OIDNode(
                    oid=oid,
                    accessible=True,
                    node_type=OIDNodeType.TABLE_ENTRY,
                    confidence=0.9,
                    last_accessed=time.time()
                )
                return node

        except Exception as e:
            logger.debug(f"Probe failed for {oid}: {e}")

        return None

    async def _discover_children(
        self,
        target: SNMPTarget,
        parent_oid: str,
        strategy: ExplorationStrategy
    ) -> List[str]:
        """Discover child OIDs of a given parent."""
        children = []

        try:
            # Use GETNEXT to discover children
            next_oid = parent_oid
            discovered_count = 0
            max_children = strategy.batch_size

            while discovered_count < max_children:
                next_response = await self.snmp_engine.get_next(target, [next_oid])

                if not next_response.success or not next_response.var_binds:
                    break

                next_oid = next_response.var_binds[0][0]

                # Check if we're still under the parent branch
                if not next_oid.startswith(parent_oid):
                    break

                # Avoid infinite loops
                if next_oid == parent_oid:
                    break

                children.append(next_oid)
                discovered_count += 1

                # Check for end-of-mib markers
                if "255.255" in next_oid or next_oid.endswith(".0"):
                    break

        except Exception as e:
            logger.debug(f"Failed to discover children for {parent_oid}: {e}")

        return children

    async def _walk_branch(
        self,
        target: SNMPTarget,
        base_oid: str,
        oid_tree: Dict[str, OIDNode],
        max_depth: int = 5
    ):
        """Walk an OID branch to discover its structure."""
        try:
            walk_response = await self.snmp_engine.walk(target, base_oid, max_repetitions=20)

            if walk_response.success and walk_response.var_binds:
                for oid_str, value in walk_response.var_binds:
                    if oid_str not in oid_tree:
                        node = OIDNode(
                            oid=oid_str,
                            accessible=True,
                            node_type=OIDNodeType.LEAF,
                            value_type=self._classify_value_type(value),
                            parent=base_oid,
                            confidence=0.8,
                            last_accessed=time.time()
                        )
                        oid_tree[oid_str] = node

        except Exception as e:
            logger.debug(f"Failed to walk branch {base_oid}: {e}")

    def _generate_oid_patterns(self, pattern: str) -> List[str]:
        """Generate OIDs from a pattern."""
        # This is a simplified pattern generator
        # In a real implementation, you'd use more sophisticated pattern matching
        oids = []

        # Extract the base prefix
        match = re.match(r"(1\.3\.6\.1\.4\.1\.(\d+))", pattern)
        if match:
            base_prefix = match.group(1)
            enterprise_id = match.group(2)

            # Generate common branch patterns
            for i in range(1, 10):
                oids.append(f"{base_prefix}.{i}")
            for i in range(1, 10):
                oids.append(f"{base_prefix}.1.{i}")
            for i in range(1, 10):
                oids.append(f"{base_prefix}.2.{i}")

        return oids

    def _classify_value_type(self, value: Any) -> str:
        """Classify the type of an SNMP value."""
        if value is None:
            return "null"

        if isinstance(value, str):
            if value.isdigit():
                return "integer"
            elif value.replace(".", "").isdigit():
                return "float"
            elif "No Such" in value or "endOfMibView" in value:
                return "error"
            else:
                return "string"

        return "unknown"

    async def _classify_nodes(self, target: SNMPTarget, oid_tree: Dict[str, OIDNode]):
        """Classify discovered nodes and extract vendor hints."""
        vendor_hints = []

        for oid, node in oid_tree.items():
            # Look for vendor-specific patterns
            for vendor, patterns in self.vendor_patterns.items():
                if any(re.search(pattern, oid) for pattern in patterns["patterns"]):
                    node.vendor_hints.append(vendor)
                    vendor_hints.append(vendor)

            # Classify node types based on OID structure
            if oid.endswith(".0") and node.accessible:
                node.node_type = OIDNodeType.SCALAR
            elif "." in oid and oid.split(".")[-1].isdigit():
                if int(oid.split(".")[-1]) > 0:
                    node.node_type = OIDNodeType.TABLE_ENTRY

        # Update confidence based on vendor hints
        for node in oid_tree.values():
            if node.vendor_hints:
                node.confidence = min(node.confidence + 0.2, 1.0)

    def _detect_vendor_from_tree(self, oid_tree: Dict[str, OIDNode]) -> List[str]:
        """Detect likely vendor from discovered OIDs."""
        vendor_votes = defaultdict(int)

        for oid, node in oid_tree.items():
            for vendor_hint in node.vendor_hints:
                vendor_votes[vendor_hint] += 1

        if vendor_votes:
            # Return vendors sorted by vote count
            return sorted(vendor_votes.keys(), key=lambda v: vendor_votes[v], reverse=True)

        return []

    async def get_device_capabilities(
        self,
        target: SNMPTarget
    ) -> Dict[str, Any]:
        """
        Analyze discovered OID tree to extract device capabilities.

        Args:
            target: SNMP target to analyze

        Returns:
            Dictionary of device capabilities
        """
        device_key = f"{target.host}:{target.port}"

        if device_key not in self.discovered_trees:
            await self.explore_device(target)

        oid_tree = self.discovered_trees[device_key]

        capabilities = {
            "vendor_hints": [],
            "device_type_hints": [],
            "supported_mibs": [],
            "data_categories": defaultdict(list),
            "accessible_oids": [],
            "total_nodes": len(oid_tree),
            "exploration_quality": 0.0
        }

        # Analyze vendor hints
        vendor_votes = defaultdict(int)
        for node in oid_tree.values():
            for vendor in node.vendor_hints:
                vendor_votes[vendor] += 1

        if vendor_votes:
            capabilities["vendor_hints"] = sorted(
                vendor_votes.keys(),
                key=lambda v: vendor_votes[v],
                reverse=True
            )

        # Categorize OIDs by functionality
        for oid, node in oid_tree.items():
            if node.accessible:
                capabilities["accessible_oids"].append(oid)

                # Categorize by OID patterns
                if "1.3.6.1.2.1.1" in oid:  # System
                    capabilities["data_categories"]["system"].append(oid)
                elif "1.3.6.1.2.1.2" in oid:  # Interfaces
                    capabilities["data_categories"]["interfaces"].append(oid)
                elif "1.3.6.1.4.1.2011.6.128" in oid:  # Huawei GPON
                    capabilities["data_categories"]["gpon"].append(oid)
                    if "olt" not in capabilities["device_type_hints"]:
                        capabilities["device_type_hints"].append("olt")
                elif "1.3.6.1.4.1.3902.110" in oid:  # ZTE GPON
                    capabilities["data_categories"]["gpon"].append(oid)
                    if "olt" not in capabilities["device_type_hints"]:
                        capabilities["device_type_hints"].append("olt")

        # Calculate exploration quality
        total_nodes = len(oid_tree)
        accessible_nodes = len(capabilities["accessible_oids"])
        categorized_nodes = sum(len(oids) for oids in capabilities["data_categories"].values())

        if total_nodes > 0:
            capabilities["exploration_quality"] = (
                (accessible_nodes / total_nodes) * 0.6 +
                (categorized_nodes / total_nodes) * 0.4
            )

        return capabilities

    def get_discovery_summary(self, target: SNMPTarget) -> Dict[str, Any]:
        """Get summary of discovery results for a device."""
        device_key = f"{target.host}:{target.port}"
        oid_tree = self.discovered_trees.get(device_key, {})

        return {
            "device": device_key,
            "total_nodes_discovered": len(oid_tree),
            "accessible_nodes": len([n for n in oid_tree.values() if n.accessible]),
            "node_types": {
                node_type.value: len([n for n in oid_tree.values() if n.node_type == node_type])
                for node_type in OIDNodeType
            },
            "vendor_hints": list(set(
                hint for node in oid_tree.values() for hint in node.vendor_hints
            )),
            "exploration_timestamp": self.exploration_stats.get(f"{device_key}_timestamp"),
            "exploration_stats": dict(self.exploration_stats)
        }

    async def close(self):
        """Close OID Explorer and cleanup resources."""
        await self.snmp_engine.close()
        self.discovered_trees.clear()
        self.exploration_cache.clear()
        self.exploration_stats.clear()