"""
Pattern Recognition - Intelligent device classification and pattern matching.

This module implements advanced pattern recognition techniques to classify
devices, detect capabilities, and identify patterns in SNMP data.
"""

import logging
import re
from typing import Dict, List, Set, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import hashlib
import difflib

from .oid_explorer import OIDExplorer, OIDNode, OIDNodeType

logger = logging.getLogger(__name__)


@dataclass
class DevicePattern:
    """Represents a device pattern for classification."""
    pattern_id: str
    name: str
    vendor: str
    device_type: str
    oid_signatures: List[str] = field(default_factory=list)
    description_patterns: List[str] = field(default_factory=list)
    behavior_patterns: Dict[str, Any] = field(default_factory=dict)
    confidence_threshold: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassificationResult:
    """Result of device classification."""
    device_id: str
    vendor: str
    device_type: str
    model: Optional[str]
    confidence: float
    evidence: Dict[str, Any]
    matched_patterns: List[str]
    alternative_classifications: List[Dict[str, Any]]


class PatternMatcher:
    """Advanced pattern matching for device classification."""

    def __init__(self):
        """Initialize pattern matcher."""
        self.patterns: Dict[str, DevicePattern] = {}
        self.similarity_cache: Dict[str, Dict[str, float]] = {}
        self._load_builtin_patterns()

    def _load_builtin_patterns(self):
        """Load built-in device patterns."""
        # Huawei OLT patterns
        self.patterns["huawei_olt_ma5800"] = DevicePattern(
            pattern_id="huawei_olt_ma5800",
            name="Huawei MA5800 OLT",
            vendor="huawei",
            device_type="olt",
            oid_signatures=[
                "1.3.6.1.4.1.2011.6.128.1.1.1",  # GPON board info
                "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.5",  # CPU usage
                "1.3.6.1.4.1.2011.6.128.1.1.3",  # ONT info
                "1.3.6.1.4.1.2011.6.128.1.1.4",  # Optical info
            ],
            description_patterns=[
                r"Huawei.*MA5800.*OLT",
                r"MA5800-[\w\d]+",
                r"VRP.*Software",
                r"HUAWEI TECH"
            ],
            behavior_patterns={
                "supports_gpon": True,
                "supports_ont_management": True,
                "has_optical_monitoring": True,
                "max_ont_per_port": 128,
                "typical_response_time_ms": 50
            }
        )

        # ZTE OLT patterns
        self.patterns["zte_olt_zxa10"] = DevicePattern(
            pattern_id="zte_olt_zxa10",
            name="ZTE ZXA10 OLT",
            vendor="zte",
            device_type="olt",
            oid_signatures=[
                "1.3.6.1.4.1.3902.110.1.1",  # Slot info
                "1.3.6.1.4.1.3902.110.1.2",  # PON port info
                "1.3.6.1.4.1.3902.110.1.3",  # ONU info
            ],
            description_patterns=[
                r"ZTE.*ZXA10.*OLT",
                r"ZXA10-[\w\d]+",
                r"ZXAN.*System",
                r"ZTE Corporation"
            ],
            behavior_patterns={
                "supports_gpon": True,
                "supports_epon": True,
                "has_slot_based_architecture": True,
                "typical_response_time_ms": 80
            }
        )

        # V-SOL OLT patterns (for undocumented devices)
        self.patterns["vsol_olt"] = DevicePattern(
            pattern_id="vsol_olt",
            name="V-SOL OLT",
            vendor="vsol",
            device_type="olt",
            oid_signatures=[
                "1.3.6.1.4.1.39926.1",      # System info
                "1.3.6.1.4.1.39926.2",      # Interface info
                "1.3.6.1.4.1.39926.3",      # GPON info
            ],
            description_patterns=[
                r"V-SOL.*OLT",
                r"V1600[\w\d]*",
                r"V2800[\w\d]*",
                r"VOLUTION"
            ],
            behavior_patterns={
                "supports_gpon": True,
                "compact_form_factor": True,
                "limited_ont_capacity": True,
                "typical_response_time_ms": 120
            }
        )

    def classify_device(
        self,
        device_id: str,
        oid_tree: Dict[str, OIDNode],
        system_info: Dict[str, Any],
        behavior_data: Dict[str, Any] = None
    ) -> ClassificationResult:
        """
        Classify a device based on discovered patterns.

        Args:
            device_id: Unique device identifier
            oid_tree: Discovered OID tree
            system_info: System information from SNMP
            behavior_data: Behavioral data (response times, etc.)

        Returns:
            Classification result with confidence scores
        """
        logger.debug(f"Classifying device {device_id}")

        # Initialize results
        pattern_scores = []
        evidence = defaultdict(list)

        # Score each pattern
        for pattern_id, pattern in self.patterns.items():
            score, pattern_evidence = self._score_pattern_match(
                pattern, oid_tree, system_info, behavior_data
            )

            if score > 0:
                pattern_scores.append((pattern, score, pattern_evidence))
                for key, value in pattern_evidence.items():
                    evidence[key].extend(value if isinstance(value, list) else [value])

        # Sort by score
        pattern_scores.sort(key=lambda x: x[1], reverse=True)

        # Determine best match
        if pattern_scores and pattern_scores[0][1] >= pattern_scores[0][0].confidence_threshold:
            best_pattern, best_score, _ = pattern_scores[0]

            # Alternative classifications
            alternatives = []
            for pattern, score, _ in pattern_scores[1:3]:  # Top 3 alternatives
                if score > 0.3:  # Only include meaningful alternatives
                    alternatives.append({
                        "vendor": pattern.vendor,
                        "device_type": pattern.device_type,
                        "model": pattern.name,
                        "confidence": score
                    })

            return ClassificationResult(
                device_id=device_id,
                vendor=best_pattern.vendor,
                device_type=best_pattern.device_type,
                model=best_pattern.name,
                confidence=best_score,
                evidence=dict(evidence),
                matched_patterns=[p[0].pattern_id for p in pattern_scores if p[1] > 0.3],
                alternative_classifications=alternatives
            )
        else:
            # No confident match found
            return ClassificationResult(
                device_id=device_id,
                vendor="unknown",
                device_type="unknown",
                model=None,
                confidence=0.0,
                evidence=dict(evidence),
                matched_patterns=[],
                alternative_classifications=[]
            )

    def _score_pattern_match(
        self,
        pattern: DevicePattern,
        oid_tree: Dict[str, OIDNode],
        system_info: Dict[str, Any],
        behavior_data: Dict[str, Any] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Score how well a pattern matches the device.

        Returns:
            Tuple of (score, evidence)
        """
        score = 0.0
        evidence = {}

        # Score OID signature matches
        oid_score, oid_evidence = self._score_oid_signatures(pattern.oid_signatures, oid_tree)
        score += oid_score * 0.4  # OID patterns are most important
        evidence["oid_matches"] = oid_evidence

        # Score description matches
        desc_score, desc_evidence = self._score_description_matches(
            pattern.description_patterns, system_info
        )
        score += desc_score * 0.3
        evidence["description_matches"] = desc_evidence

        # Score behavior pattern matches
        behavior_score, behavior_evidence = self._score_behavior_patterns(
            pattern.behavior_patterns, oid_tree, behavior_data
        )
        score += behavior_score * 0.2
        evidence["behavior_matches"] = behavior_evidence

        # Score structural patterns
        struct_score, struct_evidence = self._score_structural_patterns(pattern, oid_tree)
        score += struct_score * 0.1
        evidence["structural_matches"] = struct_evidence

        return min(score, 1.0), evidence

    def _score_oid_signatures(
        self,
        signature_oids: List[str],
        oid_tree: Dict[str, OIDNode]
    ) -> Tuple[float, List[str]]:
        """Score OID signature matches."""
        if not signature_oids:
            return 0.0, []

        matches = []
        accessible_oids = [oid for oid, node in oid_tree.items() if node.accessible]

        for signature_oid in signature_oids:
            # Exact match
            if signature_oid in oid_tree:
                matches.append(f"exact_match: {signature_oid}")
                continue

            # Prefix match (for table branches)
            for accessible_oid in accessible_oids:
                if accessible_oid.startswith(signature_oid):
                    matches.append(f"prefix_match: {accessible_oid}")
                    break

            # Similarity match
            best_match = self._find_best_oid_match(signature_oid, accessible_oids)
            if best_match and best_match[1] > 0.7:  # Similarity threshold
                matches.append(f"similar_match: {best_match[0]} (similarity: {best_match[1]:.2f})")

        score = len(matches) / len(signature_oids)
        return score, matches

    def _score_description_matches(
        self,
        description_patterns: List[str],
        system_info: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """Score description pattern matches."""
        if not description_patterns or not system_info:
            return 0.0, []

        matches = []
        description = system_info.get("description", "")
        name = system_info.get("name", "")

        for pattern in description_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                matches.append(f"description_match: {pattern}")
            if re.search(pattern, name, re.IGNORECASE):
                matches.append(f"name_match: {pattern}")

        score = len(matches) / (len(description_patterns) * 2)  # Max 2 matches per pattern
        return score, matches

    def _score_behavior_patterns(
        self,
        behavior_patterns: Dict[str, Any],
        oid_tree: Dict[str, OIDNode],
        behavior_data: Dict[str, Any] = None
    ) -> Tuple[float, List[str]]:
        """Score behavior pattern matches."""
        if not behavior_patterns:
            return 0.0, []

        matches = []
        score = 0.0

        # Check for GPON support
        if behavior_patterns.get("supports_gpon"):
            gpon_oids = [oid for oid in oid_tree.keys() if "6.128" in oid or "110" in oid]
            if gpon_oids:
                matches.append("gpon_support_detected")
                score += 0.3

        # Check for ONT management
        if behavior_patterns.get("supports_ont_management"):
            ont_oids = [oid for oid in oid_tree.keys()
                       if any(keyword in oid.lower() for keyword in ["ont", "onu", "subscriber"])]
            if ont_oids:
                matches.append("ont_management_detected")
                score += 0.2

        # Check for optical monitoring
        if behavior_patterns.get("has_optical_monitoring"):
            optical_oids = [oid for oid in oid_tree.keys()
                          if any(keyword in oid.lower() for keyword in ["optic", "power", "signal", "loss"])]
            if optical_oids:
                matches.append("optical_monitoring_detected")
                score += 0.2

        # Check response time patterns
        if behavior_data and "typical_response_time_ms" in behavior_patterns:
            actual_time = behavior_data.get("response_time_ms", 0)
            expected_time = behavior_patterns["typical_response_time_ms"]
            if abs(actual_time - expected_time) < expected_time * 0.5:
                matches.append(f"response_time_match: {actual_time}ms vs expected {expected_time}ms")
                score += 0.1

        return min(score, 1.0), matches

    def _score_structural_patterns(
        self,
        pattern: DevicePattern,
        oid_tree: Dict[str, OIDNode]
    ) -> Tuple[float, List[str]]:
        """Score structural pattern matches."""
        matches = []
        score = 0.0

        # Check OID structure complexity
        total_nodes = len(oid_tree)
        accessible_nodes = len([n for n in oid_tree.values() if n.accessible])

        if total_nodes > 50:
            matches.append("complex_oid_structure")
            score += 0.2

        if accessible_nodes / total_nodes > 0.6:
            matches.append("high_accessibility_ratio")
            score += 0.2

        # Check for enterprise-specific branches
        enterprise_oids = [oid for oid in oid_tree.keys() if "4.1." in oid]
        if len(enterprise_oids) > 5:
            matches.append("rich_enterprise_mib")
            score += 0.3

        # Check for table structures
        table_nodes = [n for n in oid_tree.values() if n.node_type == OIDNodeType.TABLE_ENTRY]
        if len(table_nodes) > 3:
            matches.append("multiple_tables_detected")
            score += 0.3

        return min(score, 1.0), matches

    def _find_best_oid_match(
        self,
        target_oid: str,
        candidate_oids: List[str]
    ) -> Optional[Tuple[str, float]]:
        """Find the best matching OID using similarity."""
        if not candidate_oids:
            return None

        best_match = None
        best_score = 0.0

        for candidate in candidate_oids:
            # Calculate similarity based on OID structure
            similarity = self._calculate_oid_similarity(target_oid, candidate)
            if similarity > best_score:
                best_score = similarity
                best_match = candidate

        return (best_match, best_score) if best_match else None

    def _calculate_oid_similarity(self, oid1: str, oid2: str) -> float:
        """Calculate similarity between two OIDs."""
        # Split OIDs into components
        parts1 = oid1.split(".")
        parts2 = oid2.split(".")

        # Calculate longest common subsequence
        lcs_length = len(list(difflib.SequenceMatcher(None, parts1, parts2).find_longest_match(
            0, len(parts1), 0, len(parts2)
        )))

        # Normalize by average length
        avg_length = (len(parts1) + len(parts2)) / 2
        similarity = lcs_length / avg_length if avg_length > 0 else 0.0

        return similarity

    def add_custom_pattern(self, pattern: DevicePattern):
        """Add a custom device pattern."""
        self.patterns[pattern.pattern_id] = pattern
        logger.info(f"Added custom pattern: {pattern.pattern_id}")

    def learn_from_device(
        self,
        device_id: str,
        oid_tree: Dict[str, OIDNode],
        system_info: Dict[str, Any],
        correct_classification: Dict[str, str]
    ) -> DevicePattern:
        """
        Learn from a device to create or improve patterns.

        Args:
            device_id: Device identifier
            oid_tree: Discovered OID tree
            system_info: System information
            correct_classification: Correct vendor, device_type, model

        Returns:
            Generated or improved pattern
        """
        logger.info(f"Learning from device {device_id}")

        # Generate pattern ID
        pattern_id = f"{correct_classification['vendor']}_{correct_classification['device_type']}"

        # Extract key OID signatures
        accessible_oids = [oid for oid, node in oid_tree.items() if node.accessible]
        key_oids = self._extract_key_oids(accessible_oids)

        # Generate description patterns
        description = system_info.get("description", "")
        desc_patterns = self._generate_description_patterns(description)

        # Analyze behavior patterns
        behavior_patterns = self._analyze_behavior_patterns(oid_tree)

        # Create new pattern
        new_pattern = DevicePattern(
            pattern_id=pattern_id,
            name=f"{correct_classification['vendor']} {correct_classification['device_type']}",
            vendor=correct_classification['vendor'],
            device_type=correct_classification['device_type'],
            oid_signatures=key_oids,
            description_patterns=desc_patterns,
            behavior_patterns=behavior_patterns,
            confidence_threshold=0.6  # Lower threshold for learned patterns
        )

        # Add to patterns
        self.add_custom_pattern(new_pattern)

        return new_pattern

    def _extract_key_oids(self, accessible_oids: List[str]) -> List[str]:
        """Extract key OIDs that are most representative."""
        # Prioritize OIDs that indicate vendor-specific functionality
        vendor_prefixes = {
            "huawei": ["2011.6.128", "2011.5.25"],
            "zte": ["3902.110"],
            "vsol": ["39926"],
            "cisco": ["9"],
            "juniper": ["2636"]
        }

        key_oids = []
        for oid in accessible_oids:
            for vendor, prefixes in vendor_prefixes.items():
                if any(prefix in oid for prefix in prefixes):
                    key_oids.append(oid)
                    break

        # If no vendor-specific OIDs found, use standard ones
        if not key_oids:
            standard_oids = [oid for oid in accessible_oids if any(
                prefix in oid for prefix in ["1.3.6.1.2.1.1", "1.3.6.1.2.1.2", "1.3.6.1.2.1.31"]
            )]
            key_oids = standard_oids[:5]  # Top 5 standard OIDs

        return key_oids[:10]  # Limit to top 10

    def _generate_description_patterns(self, description: str) -> List[str]:
        """Generate regex patterns from device description."""
        patterns = []

        if not description:
            return patterns

        # Extract key terms
        words = re.findall(r'\b[A-Za-z0-9]+\b', description)

        # Generate patterns from significant words
        significant_words = [word for word in words if len(word) > 2 and word.lower() not in [
            "the", "and", "for", "with", "com", "www", "http", "https"
        ]]

        # Create patterns
        if len(significant_words) >= 2:
            # Two-word pattern
            patterns.append(rf"{significant_words[0]}.*{significant_words[1]}")

        if len(significant_words) >= 3:
            # Three-word pattern
            patterns.append(rf"{significant_words[0]}.*{significant_words[1]}.*{significant_words[2]}")

        # Model number patterns
        model_pattern = re.search(r'\b[A-Z]+\d+[A-Z\d]*\b', description)
        if model_pattern:
            patterns.append(rf"{re.escape(model_pattern.group())}[\w\d]*")

        return patterns

    def _analyze_behavior_patterns(self, oid_tree: Dict[str, OIDNode]) -> Dict[str, Any]:
        """Analyze behavior patterns from OID tree."""
        patterns = {}

        # Detect capabilities from OID structure
        oid_strings = list(oid_tree.keys())

        # GPON detection
        gpon_indicators = ["6.128", "110", "gpon", "pon"]
        if any(indicator in " ".join(oid_strings).lower() for indicator in gpon_indicators):
            patterns["supports_gpon"] = True

        # Table detection
        table_nodes = [n for n in oid_tree.values() if n.node_type == OIDNodeType.TABLE_ENTRY]
        patterns["has_tables"] = len(table_nodes) > 0

        # Complexity assessment
        patterns["is_complex"] = len(oid_tree) > 50

        return patterns