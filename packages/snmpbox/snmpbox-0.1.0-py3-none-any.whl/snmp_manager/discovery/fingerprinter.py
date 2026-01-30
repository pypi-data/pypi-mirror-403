"""
Device Fingerprinter - Identifies and profiles network devices.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import re

from ..core.engine import SNMPEngine, SNMPTarget

logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """Device types for telecom equipment."""
    UNKNOWN = "unknown"
    OLT = "olt"
    ONU = "onu"
    SWITCH = "switch"
    ROUTER = "router"
    BSC = "bsc"
    RNC = "rnc"
    SMSC = "smsc"
    BTS = "bts"
    MESH = "mesh"
    GENERAL = "general"


class Vendor(Enum):
    """Known telecom vendors."""
    UNKNOWN = "unknown"
    HUAWEI = "huawei"
    ZTE = "zte"
    VSOL = "vsol"
    FIBERHOME = "fiberhome"
    CDATA = "c-data"
    CISCO = "cisco"
    JUNIPER = "juniper"
    NOKIA = "nokia"
    ERICSSON = "ericsson"
    MIKROTIK = "mikrotik"
    TP_LINK = "tp-link"


@dataclass
class DeviceSignature:
    """Device signature for identification."""
    vendor: Vendor
    device_type: DeviceType
    model: Optional[str]
    firmware_version: Optional[str]
    confidence: float  # 0.0 to 1.0
    evidence: Dict[str, Any]


@dataclass
class DeviceProfile:
    """Complete device profile."""
    ip: str
    signature: DeviceSignature
    capabilities: List[str]
    oid_patterns: Dict[str, List[str]]
    system_info: Dict[str, Any]
    interface_info: List[Dict[str, Any]]
    custom_oids: Dict[str, str]


class DeviceFingerprinter:
    """
    Intelligent device fingerprinting system.

    Features:
    - Multi-pattern matching for device identification
    - OID tree analysis for capability detection
    - Firmware version detection
    - Vendor-specific pattern recognition
    - Confidence scoring for identification
    """

    def __init__(self):
        """Initialize fingerprinter with pattern database."""
        self.snmp_engine = SNMPEngine()
        self._load_pattern_database()

    def _load_pattern_database(self):
        """Load device identification patterns."""
        self.vendor_patterns = {
            Vendor.HUAWEI: {
                "description_patterns": [
                    r"Huawei.*OLT",
                    r"MA5800",
                    r"MA5616",
                    r"Huawei.*Technologies",
                    r"VRP.*software"
                ],
                "oid_prefixes": [
                    "1.3.6.1.4.1.2011",
                    "1.3.6.1.4.1.2011.6.128",  # GPON
                    "1.3.6.1.4.1.2011.5.25"   # Huawei MIB
                ],
                "system_object_ids": [
                    "1.3.6.1.4.1.2011.2",  # Huawei devices
                ]
            },
            Vendor.ZTE: {
                "description_patterns": [
                    r"ZTE.*OLT",
                    r"ZXA10",
                    r"ZTE.*Corporation",
                    r"ZXAN"
                ],
                "oid_prefixes": [
                    "1.3.6.1.4.1.3902",
                    "1.3.6.1.4.1.3902.110",  # ZTE GPON
                ],
                "system_object_ids": [
                    "1.3.6.1.4.1.3902.1",
                ]
            },
            Vendor.VSOL: {
                "description_patterns": [
                    r"V-SOL",
                    r"VOLUTION",
                    r"V1600D",
                    r"V2801RH"
                ],
                "oid_prefixes": [
                    "1.3.6.1.4.1.39926",  # V-SOL enterprise
                ],
                "system_object_ids": [
                    "1.3.6.1.4.1.39926.1",
                ]
            },
            Vendor.FIBERHOME: {
                "description_patterns": [
                    r"FiberHome",
                    r"AN5506",
                    r"AN5116",
                    r"HG"
                ],
                "oid_prefixes": [
                    "1.3.6.1.4.1.86",  # Fiberhome
                ],
                "system_object_ids": [
                    "1.3.6.1.4.1.86.1",
                ]
            }
        }

        self.device_type_patterns = {
            DeviceType.OLT: {
                "description_patterns": [
                    r"OLT",
                    r"Optical.*Line.*Terminal",
                    r"GPON.*OLT",
                    r"EPON.*OLT"
                ],
                "interface_patterns": [
                    r"gpon",
                    r"epon",
                    r"pon",
                    r"optical"
                ],
                "capability_oids": [
                    "1.3.6.1.4.1.2011.6.128",  # Huawei GPON
                    "1.3.6.1.4.1.3902.110",  # ZTE GPON
                ]
            },
            DeviceType.ONU: {
                "description_patterns": [
                    r"ONU",
                    r"Optical.*Network.*Unit",
                    r"ONT",
                    r"Optical.*Network.*Terminal"
                ],
                "interface_patterns": [
                    r"eth",
                    r"pon",
                    r"uni"
                ],
                "capability_oids": [
                    # ONU specific OIDs
                ]
            },
            DeviceType.SWITCH: {
                "description_patterns": [
                    r"Switch",
                    r"Ethernet.*Switch",
                    r"Network.*Switch"
                ],
                "interface_patterns": [
                    r"ethernet",
                    r"fastethernet",
                    r"gigabitethernet"
                ]
            },
            DeviceType.ROUTER: {
                "description_patterns": [
                    r"Router",
                    r"Broadband.*Router",
                    r"IP.*Router"
                ],
                "interface_patterns": [
                    r"serial",
                    r"ethernet",
                    r"tunnel"
                ]
            }
        }

    async def fingerprint_device(self, target: SNMPTarget, basic_info: Dict[str, Any] = None) -> DeviceSignature:
        """
        Perform device fingerprinting.

        Args:
            target: SNMP target to fingerprint
            basic_info: Previously collected basic device info

        Returns:
            DeviceSignature with identification results
        """
        logger.info(f"Fingerprinting device: {target.host}")

        evidence = {}
        confidence_scores = []

        # Use provided basic info or collect it
        if not basic_info:
            basic_info = await self._collect_basic_info(target)

        # Analyze system description
        if basic_info.get("description"):
            desc_vendor, desc_confidence = self._identify_vendor_from_description(
                basic_info["description"]
            )
            if desc_vendor != Vendor.UNKNOWN:
                evidence["description_vendor"] = desc_vendor.value
                confidence_scores.append(desc_confidence)

            desc_type, type_confidence = self._identify_device_type_from_description(
                basic_info["description"]
            )
            if desc_type != DeviceType.UNKNOWN:
                evidence["description_device_type"] = desc_type.value
                confidence_scores.append(type_confidence)

        # Analyze enterprise OID
        if basic_info.get("enterprise_oid"):
            oid_vendor, oid_confidence = self._identify_vendor_from_enterprise_oid(
                basic_info["enterprise_oid"]
            )
            if oid_vendor != Vendor.UNKNOWN:
                evidence["enterprise_oid_vendor"] = oid_vendor.value
                confidence_scores.append(oid_confidence)

        # Try OID tree probing
        oid_evidence = await self._probe_oid_tree(target)
        evidence.update(oid_evidence)
        if oid_evidence.get("vendor_confidence"):
            confidence_scores.append(oid_evidence["vendor_confidence"])

        # Try vendor-specific OIDs
        vendor_specific_evidence = await self._probe_vendor_specific_oids(target)
        evidence.update(vendor_specific_evidence)
        if vendor_specific_evidence.get("vendor_confidence"):
            confidence_scores.append(vendor_specific_evidence["vendor_confidence"])

        # Determine final vendor and device type
        vendor = self._determine_vendor(evidence)
        device_type = self._determine_device_type(evidence, vendor)

        # Extract model and firmware
        model = self._extract_model(basic_info.get("description", ""), vendor)
        firmware = self._extract_firmware_version(basic_info.get("description", ""))

        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        signature = DeviceSignature(
            vendor=vendor,
            device_type=device_type,
            model=model,
            firmware_version=firmware,
            confidence=min(overall_confidence, 1.0),
            evidence=evidence
        )

        logger.info(f"Fingerprinted {target.host}: {vendor.value} {device_type.value} "
                   f"(confidence: {overall_confidence:.2f})")

        return signature

    async def _collect_basic_info(self, target: SNMPTarget) -> Dict[str, Any]:
        """Collect basic device information for fingerprinting."""
        basic_info = {}

        try:
            # System information
            system_oids = [
                "1.3.6.1.2.1.1.1.0",  # System description
                "1.3.6.1.2.1.1.2.0",  # System OID
                "1.3.6.1.2.1.1.3.0",  # System uptime
                "1.3.6.1.2.1.1.5.0",  # System name
            ]

            response = await self.snmp_engine.get(target, system_oids)
            if response.success and response.var_binds:
                for oid_str, value in response.var_binds:
                    if "1.3.6.1.2.1.1.1.0" in oid_str:
                        basic_info["description"] = value
                    elif "1.3.6.1.2.1.1.2.0" in oid_str:
                        basic_info["enterprise_oid"] = value
                    elif "1.3.6.1.2.1.1.5.0" in oid_str:
                        basic_info["hostname"] = value

        except Exception as e:
            logger.error(f"Failed to collect basic info from {target.host}: {e}")

        return basic_info

    def _identify_vendor_from_description(self, description: str) -> Tuple[Vendor, float]:
        """Identify vendor from system description."""
        description_lower = description.lower()

        for vendor, patterns in self.vendor_patterns.items():
            for pattern in patterns.get("description_patterns", []):
                if re.search(pattern, description_lower, re.IGNORECASE):
                    # Return confidence based on match specificity
                    confidence = 0.8 if vendor.name.lower() in description_lower else 0.6
                    return vendor, confidence

        return Vendor.UNKNOWN, 0.0

    def _identify_device_type_from_description(self, description: str) -> Tuple[DeviceType, float]:
        """Identify device type from system description."""
        description_lower = description.lower()

        for device_type, patterns in self.device_type_patterns.items():
            for pattern in patterns.get("description_patterns", []):
                if re.search(pattern, description_lower, re.IGNORECASE):
                    return device_type, 0.7

        return DeviceType.UNKNOWN, 0.0

    def _identify_vendor_from_enterprise_oid(self, enterprise_oid: str) -> Tuple[Vendor, float]:
        """Identify vendor from enterprise OID."""
        for vendor, patterns in self.vendor_patterns.items():
            for oid_prefix in patterns.get("oid_prefixes", []):
                if enterprise_oid.startswith(oid_prefix):
                    return vendor, 0.9  # High confidence for OID match

        return Vendor.UNKNOWN, 0.0

    async def _probe_oid_tree(self, target: SNMPTarget) -> Dict[str, Any]:
        """Probe OID tree for vendor-specific patterns."""
        evidence = {}
        max_confidence = 0.0

        # Try common vendor-specific OID branches
        vendor_oid_tests = {
            Vendor.HUAWEI: [
                "1.3.6.1.4.1.2011.6.128.1.1",  # Huawei GPON
                "1.3.6.1.4.1.2011.5.25.31.1",   # Huawei device info
            ],
            Vendor.ZTE: [
                "1.3.6.1.4.1.3902.110.1.1",     # ZTE GPON
                "1.3.6.1.4.1.3902.1.1",         # ZTE system
            ],
            Vendor.VSOL: [
                "1.3.6.1.4.1.39926.100.1",      # V-SOL system
            ]
        }

        for vendor, oid_list in vendor_oid_tests.items():
            accessible_oids = 0
            total_oids = len(oid_list)

            for oid in oid_list:
                response = await self.snmp_engine.get(target, [oid])
                if response.success:
                    accessible_oids += 1

            if accessible_oids > 0:
                confidence = accessible_oids / total_oids
                if confidence > max_confidence:
                    max_confidence = confidence
                    evidence["oid_tree_vendor"] = vendor.value

        if max_confidence > 0:
            evidence["vendor_confidence"] = max_confidence

        return evidence

    async def _probe_vendor_specific_oids(self, target: SNMPTarget) -> Dict[str, Any]:
        """Probe vendor-specific OIDs for identification."""
        evidence = {}

        # Test for GPON capabilities (OLT devices)
        gpon_oids = [
            "1.3.6.1.4.1.2011.6.128.1.1.1",  # Huawei GPON board
            "1.3.6.1.4.1.3902.110.1.1",     # ZTE GPON
        ]

        gpon_accessible = 0
        for oid in gpon_oids:
            response = await self.snmp_engine.get(target, [oid])
            if response.success:
                gpon_accessible += 1

        if gpon_accessible > 0:
            evidence["gpon_capable"] = True
            evidence["device_type_hint"] = "olt"

        return evidence

    def _determine_vendor(self, evidence: Dict[str, Any]) -> Vendor:
        """Determine most likely vendor based on evidence."""
        vendor_votes = {}

        # Count votes from different evidence sources
        for key, value in evidence.items():
            if "vendor" in key and isinstance(value, str):
                try:
                    vendor = Vendor(value.lower())
                    vendor_votes[vendor] = vendor_votes.get(vendor, 0) + 1
                except ValueError:
                    pass

        # Return vendor with most votes
        if vendor_votes:
            return max(vendor_votes.items(), key=lambda x: x[1])[0]

        return Vendor.UNKNOWN

    def _determine_device_type(self, evidence: Dict[str, Any], vendor: Vendor) -> DeviceType:
        """Determine device type based on evidence and vendor."""
        # Check for explicit device type hints
        if evidence.get("device_type_hint"):
            try:
                return DeviceType(evidence["device_type_hint"])
            except ValueError:
                pass

        # Check GPON capabilities
        if evidence.get("gpon_capable"):
            return DeviceType.OLT

        # Vendor-specific device type logic
        if vendor in [Vendor.HUAWEI, Vendor.ZTE, Vendor.VSOL]:
            # These vendors primarily make telecom equipment
            return DeviceType.OLT

        return DeviceType.GENERAL

    def _extract_model(self, description: str, vendor: Vendor) -> Optional[str]:
        """Extract model number from description."""
        # Model extraction patterns by vendor
        if vendor == Vendor.HUAWEI:
            patterns = [
                r"MA5800[\w-]*",
                r"MA5616[\w-]*",
                r"S\d+[\w-]*",
            ]
        elif vendor == Vendor.ZTE:
            patterns = [
                r"ZXA10[\w-]*",
                r"ZTE[\w-]*",
                r"ZXAN[\w-]*",
            ]
        elif vendor == Vendor.VSOL:
            patterns = [
                r"V\d+[DRH]*[\w-]*",
                r"V-SOL[\w-]*",
            ]
        else:
            return None

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group().strip()

        return None

    def _extract_firmware_version(self, description: str) -> Optional[str]:
        """Extract firmware version from description."""
        # Common version patterns
        version_patterns = [
            r"V\d+R\d+[C\d]*",
            r"Version\s+[\d.]+",
            r"v[\d.]+",
            r"Release\s+[\d.]+",
        ]

        for pattern in version_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group().strip()

        return None

    async def close(self):
        """Close fingerprinter and cleanup resources."""
        await self.snmp_engine.close()