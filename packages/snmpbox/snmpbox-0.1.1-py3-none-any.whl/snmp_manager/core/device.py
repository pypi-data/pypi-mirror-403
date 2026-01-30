"""
Device class - Represents and manages network devices.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json

from .engine import SNMPEngine, SNMPTarget, SNMPVersion
from ..discovery.fingerprinter import DeviceFingerprinter, DeviceSignature, DeviceType, Vendor

logger = logging.getLogger(__name__)


class DeviceStatus(Enum):
    """Device operational status."""
    UNKNOWN = "unknown"
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class DeviceMetrics:
    """Device performance metrics."""
    response_time_ms: float
    snmp_errors: int
    successful_collections: int
    last_collection: Optional[datetime]
    uptime_seconds: Optional[int]
    cpu_usage_percent: Optional[float]
    memory_usage_percent: Optional[float]


class Device:
    """
    Represents a network device with collection and profiling capabilities.

    Features:
    - Automatic data collection with retry logic
    - Device fingerprinting and profiling
    - Performance metrics tracking
    - Error handling and status monitoring
    - Data normalization and output formatting
    """

    def __init__(
        self,
        host: str,
        port: int = 161,
        community: str = "public",
        version: SNMPVersion = SNMPVersion.V2C,
        timeout: int = 5,
        retries: int = 3,
        device_info: Dict[str, Any] = None
    ):
        """
        Initialize device.

        Args:
            host: Device IP address or hostname
            port: SNMP port (default: 161)
            community: SNMP community string
            version: SNMP version
            timeout: SNMP timeout in seconds
            retries: Number of retry attempts
            device_info: Pre-collected device information
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self.device_info = device_info or {}

        # Create SNMP target
        self.target = SNMPTarget(
            host=host,
            port=port,
            timeout=timeout,
            retries=retries
        )
        self.target.credentials.community = community
        self.target.credentials.version = version

        # Initialize components
        self.snmp_engine = SNMPEngine()
        self.fingerprinter = DeviceFingerprinter()

        # Device state
        self.signature: Optional[DeviceSignature] = None
        self.status = DeviceStatus.UNKNOWN
        self.metrics = DeviceMetrics(
            response_time_ms=0.0,
            snmp_errors=0,
            successful_collections=0,
            last_collection=None,
            uptime_seconds=None,
            cpu_usage_percent=None,
            memory_usage_percent=None
        )

        # Cached data
        self._cached_data: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_minutes = 5

    async def initialize(self) -> bool:
        """
        Initialize device and perform basic profiling.

        Returns:
            True if initialization successful, False otherwise
        """
        logger.info(f"Initializing device: {self.host}")

        try:
            # Test SNMP connectivity
            if not await self.snmp_engine.test_connection(self.target):
                logger.error(f"SNMP connection failed for {self.host}")
                self.status = DeviceStatus.OFFLINE
                return False

            self.status = DeviceStatus.ONLINE

            # Perform device fingerprinting
            basic_info = self.device_info
            self.signature = await self.fingerprinter.fingerprint_device(
                self.target, basic_info
            )

            logger.info(f"Device {self.host} initialized: "
                       f"{self.signature.vendor.value} {self.signature.device_type.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize device {self.host}: {e}")
            self.status = DeviceStatus.ERROR
            return False

    async def collect(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Collect complete device data.

        Args:
            force_refresh: Ignore cache and force fresh collection

        Returns:
            Complete device data dictionary
        """
        # Check cache
        if not force_refresh and self._is_cache_valid():
            logger.debug(f"Using cached data for {self.host}")
            return self._cached_data

        logger.info(f"Collecting data from device: {self.host}")
        start_time = datetime.now()

        try:
            # Initialize if not already done
            if self.signature is None:
                await self.initialize()

            # Collect data based on device type and vendor
            if self.signature:
                data = await self._collect_by_device_type()
            else:
                data = await self._collect_generic_data()

            # Add metadata
            data["metadata"] = self._get_collection_metadata(start_time)
            data["identification"] = self._get_identification_info()

            # Update metrics
            self._update_metrics(start_time, True)

            # Cache the results
            self._cached_data = data
            self._cache_timestamp = datetime.now()

            return data

        except Exception as e:
            logger.error(f"Data collection failed for {self.host}: {e}")
            self.status = DeviceStatus.ERROR
            self._update_metrics(start_time, False)
            raise

    async def _collect_by_device_type(self) -> Dict[str, Any]:
        """Collect data based on device type."""
        device_type = self.signature.device_type

        if device_type == DeviceType.OLT:
            return await self._collect_olt_data()
        elif device_type == DeviceType.ONU:
            return await self._collect_onu_data()
        elif device_type == DeviceType.SWITCH:
            return await self._collect_switch_data()
        elif device_type == DeviceType.ROUTER:
            return await self._collect_router_data()
        else:
            return await self._collect_generic_data()

    async def _collect_olt_data(self) -> Dict[str, Any]:
        """Collect OLT-specific data."""
        data = await self._collect_generic_data()

        vendor = self.signature.vendor

        # Vendor-specific OLT data collection
        if vendor == Vendor.HUAWEI:
            olt_data = await self._collect_huawei_olt_data()
        elif vendor == Vendor.ZTE:
            olt_data = await self._collect_zte_olt_data()
        elif vendor == Vendor.VSOL:
            olt_data = await self._collect_vsol_olt_data()
        else:
            olt_data = await self._collect_generic_olt_data()

        data["olt_specific"] = olt_data
        return data

    async def _collect_huawei_olt_data(self) -> Dict[str, Any]:
        """Collect Huawei OLT specific data."""
        olt_data = {}

        # Huawei OLT MIBs
        huawei_oids = {
            "board_info": "1.3.6.1.4.1.2011.6.128.1.1.1",
            "pon_ports": "1.3.6.1.4.1.2011.6.128.1.1.2",
            "ont_info": "1.3.6.1.4.1.2011.6.128.1.1.3",
            "optical_info": "1.3.6.1.4.1.2011.6.128.1.1.4",
        }

        for key, oid in huawei_oids.items():
            try:
                response = await self.snmp_engine.walk(self.target, oid)
                if response.success and response.var_binds:
                    olt_data[key] = response.var_binds
            except Exception as e:
                logger.debug(f"Failed to collect {key} from Huawei OLT: {e}")

        return olt_data

    async def _collect_zte_olt_data(self) -> Dict[str, Any]:
        """Collect ZTE OLT specific data."""
        olt_data = {}

        # ZTE OLT MIBs
        zte_oids = {
            "slot_info": "1.3.6.1.4.1.3902.110.1.1",
            "pon_port_info": "1.3.6.1.4.1.3902.110.1.2",
            "onu_info": "1.3.6.1.4.1.3902.110.1.3",
        }

        for key, oid in zte_oids.items():
            try:
                response = await self.snmp_engine.walk(self.target, oid)
                if response.success and response.var_binds:
                    olt_data[key] = response.var_binds
            except Exception as e:
                logger.debug(f"Failed to collect {key} from ZTE OLT: {e}")

        return olt_data

    async def _collect_vsol_olt_data(self) -> Dict[str, Any]:
        """Collect V-SOL OLT specific data."""
        olt_data = {}

        # V-SOL OLT MIBs (these might need to be discovered through probing)
        vsol_oids = {
            "system_info": "1.3.6.1.4.1.39926.1",
            "interface_info": "1.3.6.1.4.1.39926.2",
            "gpon_info": "1.3.6.1.4.1.39926.3",
        }

        for key, oid in vsol_oids.items():
            try:
                response = await self.snmp_engine.walk(self.target, oid)
                if response.success and response.var_binds:
                    olt_data[key] = response.var_binds
            except Exception as e:
                logger.debug(f"Failed to collect {key} from V-SOL OLT: {e}")

        return olt_data

    async def _collect_generic_olt_data(self) -> Dict[str, Any]:
        """Collect generic OLT data when vendor is unknown."""
        olt_data = {}

        # Try common OLT OIDs
        common_oids = {
            "interface_table": "1.3.6.1.2.1.2.2",
            "system_group": "1.3.6.1.2.1.1",
            "interface_group": "1.3.6.1.2.1.31.1",
        }

        for key, oid in common_oids.items():
            try:
                response = await self.snmp_engine.walk(self.target, oid)
                if response.success and response.var_binds:
                    olt_data[key] = response.var_binds
            except Exception as e:
                logger.debug(f"Failed to collect {key} from generic OLT: {e}")

        return olt_data

    async def _collect_onu_data(self) -> Dict[str, Any]:
        """Collect ONU-specific data."""
        data = await self._collect_generic_data()
        onu_data = {}

        # ONU specific collections
        onu_oids = {
            "optical_info": "1.3.6.1.4.1.2011.6.128.1.1.6",  # Huawei ONT optical
            "service_config": "1.3.6.1.4.1.2011.6.128.1.1.7",  # Huawei ONT config
        }

        for key, oid in onu_oids.items():
            try:
                response = await self.snmp_engine.get(self.target, [oid])
                if response.success and response.var_binds:
                    onu_data[key] = dict(response.var_binds)
            except Exception as e:
                logger.debug(f"Failed to collect {key} from ONU: {e}")

        data["onu_specific"] = onu_data
        return data

    async def _collect_switch_data(self) -> Dict[str, Any]:
        """Collect switch-specific data."""
        data = await self._collect_generic_data()
        switch_data = {}

        # Switch specific collections
        switch_oids = {
            "bridge_mib": "1.3.6.1.2.1.17",
            "vlan_table": "1.3.6.1.2.1.17.7",
            "dot1d_base": "1.3.6.1.2.1.17.1",
        }

        for key, oid in switch_oids.items():
            try:
                response = await self.snmp_engine.walk(self.target, oid)
                if response.success and response.var_binds:
                    switch_data[key] = response.var_binds
            except Exception as e:
                logger.debug(f"Failed to collect {key} from switch: {e}")

        data["switch_specific"] = switch_data
        return data

    async def _collect_router_data(self) -> Dict[str, Any]:
        """Collect router-specific data."""
        data = await self._collect_generic_data()
        router_data = {}

        # Router specific collections
        router_oids = {
            "ip_route_table": "1.3.6.1.2.1.4.21",
            "ip_forwarding": "1.3.6.1.2.1.4.1",
            "icmp_stats": "1.3.6.1.2.1.5",
        }

        for key, oid in router_oids.items():
            try:
                response = await self.snmp_engine.get(self.target, [oid])
                if response.success and response.var_binds:
                    router_data[key] = dict(response.var_binds)
            except Exception as e:
                logger.debug(f"Failed to collect {key} from router: {e}")

        data["router_specific"] = router_data
        return data

    async def _collect_generic_data(self) -> Dict[str, Any]:
        """Collect generic device data."""
        data = {}

        # Standard system information
        system_oids = [
            "1.3.6.1.2.1.1.1.0",  # System description
            "1.3.6.1.2.1.1.3.0",  # System uptime
            "1.3.6.1.2.1.1.4.0",  # System contact
            "1.3.6.1.2.1.1.5.0",  # System name
            "1.3.6.1.2.1.1.6.0",  # System location
            "1.3.6.1.2.1.1.2.0",  # System OID
        ]

        try:
            response = await self.snmp_engine.get(self.target, system_oids)
            if response.success and response.var_binds:
                system_info = {}
                for oid_str, value in response.var_binds:
                    if "1.3.6.1.2.1.1.1.0" in oid_str:
                        system_info["description"] = value
                    elif "1.3.6.1.2.1.1.3.0" in oid_str:
                        system_info["uptime_ticks"] = value
                    elif "1.3.6.1.2.1.1.4.0" in oid_str:
                        system_info["contact"] = value
                    elif "1.3.6.1.2.1.1.5.0" in oid_str:
                        system_info["name"] = value
                    elif "1.3.6.1.2.1.1.6.0" in oid_str:
                        system_info["location"] = value
                    elif "1.3.6.1.2.1.1.2.0" in oid_str:
                        system_info["object_id"] = value

                data["system"] = system_info

        except Exception as e:
            logger.error(f"Failed to collect system data: {e}")

        # Interface information
        try:
            interface_response = await self.snmp_engine.walk(self.target, "1.3.6.1.2.1.2.2")
            if interface_response.success and interface_response.var_binds:
                data["interfaces"] = interface_response.var_binds
        except Exception as e:
            logger.error(f"Failed to collect interface data: {e}")

        return data

    def _get_collection_metadata(self, start_time: datetime) -> Dict[str, Any]:
        """Get collection metadata."""
        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        return {
            "collector_version": "0.1.1",
            "collection_timestamp": end_time.isoformat(),
            "collection_duration_ms": duration_ms,
            "device_host": self.host,
            "device_port": self.port,
            "snmp_version": self.target.credentials.version.name,
            "collection_method": "snmp_manager"
        }

    def _get_identification_info(self) -> Dict[str, Any]:
        """Get device identification information."""
        identification = {
            "device_id": f"{self.host}:{self.port}",
            "device_type": "unknown",
            "vendor": "unknown",
            "model": None,
            "firmware_version": None,
        }

        if self.signature:
            identification.update({
                "device_type": self.signature.device_type.value,
                "vendor": self.signature.vendor.value,
                "model": self.signature.model,
                "firmware_version": self.signature.firmware_version,
                "identification_confidence": self.signature.confidence
            })

        return identification

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self._cached_data or not self._cache_timestamp:
            return False

        age_minutes = (datetime.now() - self._cache_timestamp).total_seconds() / 60
        return age_minutes < self._cache_ttl_minutes

    def _update_metrics(self, start_time: datetime, success: bool):
        """Update device performance metrics."""
        end_time = datetime.now()
        response_time_ms = (end_time - start_time).total_seconds() * 1000

        self.metrics.response_time_ms = response_time_ms
        self.metrics.last_collection = end_time

        if success:
            self.metrics.successful_collections += 1
        else:
            self.metrics.snmp_errors += 1

    def to_json(self) -> str:
        """Convert device data to JSON string."""
        return json.dumps(self._cached_data, indent=2, default=str)

    def to_dict(self) -> Dict[str, Any]:
        """Convert device data to dictionary."""
        return self._cached_data or {}

    async def close(self):
        """Close device and cleanup resources."""
        await self.snmp_engine.close()
        await self.fingerprinter.close()

    def __str__(self) -> str:
        """String representation of device."""
        return f"Device({self.host}, {self.signature.vendor.value if self.signature else 'Unknown'})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"Device(host='{self.host}', port={self.port}, "
                f"vendor='{self.signature.vendor.value if self.signature else 'Unknown'}, "
                f"type='{self.signature.device_type.value if self.signature else 'Unknown'}')")