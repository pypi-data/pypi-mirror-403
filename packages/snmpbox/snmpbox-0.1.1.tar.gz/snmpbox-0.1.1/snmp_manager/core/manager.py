"""
SNMP Manager - Main management interface for device discovery and collection.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from ipaddress import ip_network

from .device import Device, DeviceStatus
from .engine import SNMPEngine, SNMPTarget, SNMPVersion
from ..discovery.scanner import NetworkScanner
from ..discovery.fingerprinter import DeviceFingerprinter, DeviceType, Vendor

logger = logging.getLogger(__name__)


class SNMPManager:
    """
    Main SNMP Manager class for device discovery and data collection.

    Features:
    - Network scanning and device discovery
    - Automatic device fingerprinting
    - Batch data collection
    - Performance monitoring
    - Error handling and retry logic
    - Multiple output formats
    """

    def __init__(
        self,
        max_concurrent_operations: int = 50,
        default_community: str = "public",
        default_version: SNMPVersion = SNMPVersion.V2C,
        default_timeout: int = 5,
        default_retries: int = 3
    ):
        """
        Initialize SNMP Manager.

        Args:
            max_concurrent_operations: Maximum concurrent operations
            default_community: Default SNMP community string
            default_version: Default SNMP version
            default_timeout: Default SNMP timeout
            default_retries: Default SNMP retry count
        """
        self.max_concurrent_operations = max_concurrent_operations
        self.default_community = default_community
        self.default_version = default_version
        self.default_timeout = default_timeout
        self.default_retries = default_retries

        # Initialize components
        self.snmp_engine = SNMPEngine(max_concurrent_requests=max_concurrent_operations)
        self.scanner = NetworkScanner(max_concurrent_scans=max_concurrent_operations)
        self.fingerprinter = DeviceFingerprinter()

        # Device registry
        self.devices: Dict[str, Device] = {}

        # Statistics
        self.stats = {
            "total_discoveries": 0,
            "total_collections": 0,
            "successful_collections": 0,
            "failed_collections": 0,
            "start_time": datetime.now()
        }

    @classmethod
    async def discover(
        cls,
        network_range: str,
        communities: List[str] = None,
        ports: List[int] = None,
        **kwargs
    ) -> List[Device]:
        """
        Discover SNMP devices on network.

        Args:
            network_range: Network range in CIDR format
            communities: List of SNMP communities to try
            ports: List of ports to scan
            **kwargs: Additional manager parameters

        Returns:
            List of discovered Device objects
        """
        manager = cls(**kwargs)
        return await manager.discover_devices(network_range, communities, ports)

    async def discover_devices(
        self,
        network_range: str,
        communities: List[str] = None,
        ports: List[int] = None
    ) -> List[Device]:
        """
        Discover devices on specified network range.

        Args:
            network_range: Network range in CIDR format
            communities: List of SNMP communities to try
            ports: List of ports to scan

        Returns:
            List of discovered Device objects
        """
        logger.info(f"Starting device discovery on {network_range}")
        self.stats["total_discoveries"] += 1

        if communities is None:
            communities = [self.default_community]

        if ports is None:
            ports = [161, 162]

        # Scan network
        discovered_raw = await self.scanner.scan_network_range(
            network_range=network_range,
            ports=ports,
            communities=communities
        )

        logger.info(f"Found {len(discovered_raw)} potential SNMP devices")

        # Create Device objects
        discovered_devices = []
        for device_info in discovered_raw:
            device = Device(
                host=device_info["ip"],
                port=device_info["port"],
                community=device_info["community"],
                version=self.default_version,
                timeout=self.default_timeout,
                retries=self.default_retries,
                device_info=device_info
            )

            # Add to registry
            device_key = f"{device.host}:{device.port}"
            self.devices[device_key] = device
            discovered_devices.append(device)

        return discovered_devices

    async def discover_local_network(self) -> List[Device]:
        """
        Discover devices on local network using ARP table.

        Returns:
            List of discovered Device objects
        """
        logger.info("Starting local network discovery")

        # Scan ARP table
        discovered_raw = await self.scanner.discover_local_network()

        # Create Device objects
        discovered_devices = []
        for device_info in discovered_raw:
            device = Device(
                host=device_info["ip"],
                port=device_info["port"],
                community=device_info["community"],
                version=self.default_version,
                timeout=self.default_timeout,
                retries=self.default_retries,
                device_info=device_info
            )

            # Add to registry
            device_key = f"{device.host}:{device.port}"
            self.devices[device_key] = device
            discovered_devices.append(device)

        return discovered_devices

    async def add_device(
        self,
        host: str,
        port: int = 161,
        community: str = None,
        version: SNMPVersion = None,
        timeout: int = None,
        retries: int = None
    ) -> Device:
        """
        Add a single device to the manager.

        Args:
            host: Device IP address or hostname
            port: SNMP port
            community: SNMP community string
            version: SNMP version
            timeout: SNMP timeout
            retries: SNMP retry count

        Returns:
            Device object
        """
        device = Device(
            host=host,
            port=port,
            community=community or self.default_community,
            version=version or self.default_version,
            timeout=timeout or self.default_timeout,
            retries=retries or self.default_retries
        )

        # Add to registry
        device_key = f"{device.host}:{device.port}"
        self.devices[device_key] = device

        return device

    async def collect_all(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Collect data from all registered devices.

        Args:
            force_refresh: Ignore cache and force fresh collection

        Returns:
            List of device data dictionaries
        """
        logger.info(f"Starting data collection from {len(self.devices)} devices")
        self.stats["total_collections"] += 1

        if not self.devices:
            logger.warning("No devices registered for collection")
            return []

        # Create collection tasks
        tasks = []
        for device in self.devices.values():
            task = self._collect_device_safe(device, force_refresh)
            tasks.append(task)

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, dict):
                successful_results.append(result)
                self.stats["successful_collections"] += 1
            else:
                logger.error(f"Collection failed for device {i}: {result}")
                self.stats["failed_collections"] += 1

        logger.info(f"Collection completed: {len(successful_results)}/{len(self.devices)} successful")
        return successful_results

    async def _collect_device_safe(self, device: Device, force_refresh: bool) -> Dict[str, Any]:
        """Collect device data with error handling."""
        try:
            return await device.collect(force_refresh=force_refresh)
        except Exception as e:
            logger.error(f"Failed to collect from {device.host}: {e}")
            return {
                "error": str(e),
                "device_host": device.host,
                "collection_failed": True
            }

    async def collect_device(
        self,
        host: str,
        port: int = 161,
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Collect data from specific device.

        Args:
            host: Device IP address or hostname
            port: SNMP port
            force_refresh: Ignore cache and force fresh collection

        Returns:
            Device data dictionary or None if failed
        """
        device_key = f"{host}:{port}"
        device = self.devices.get(device_key)

        if not device:
            logger.error(f"Device {device_key} not found in registry")
            return None

        try:
            return await device.collect(force_refresh=force_refresh)
        except Exception as e:
            logger.error(f"Failed to collect from {device_key}: {e}")
            return None

    async def filter_devices(
        self,
        vendor: Optional[Union[Vendor, str]] = None,
        device_type: Optional[Union[DeviceType, str]] = None,
        status: Optional[DeviceStatus] = None
    ) -> List[Device]:
        """
        Filter devices by various criteria.

        Args:
            vendor: Filter by vendor
            device_type: Filter by device type
            status: Filter by device status

        Returns:
            List of filtered Device objects
        """
        filtered_devices = []

        for device in self.devices.values():
            # Initialize device if not already done
            if device.signature is None:
                await device.initialize()

            # Apply filters
            if vendor and device.signature:
                if isinstance(vendor, str):
                    if device.signature.vendor.value.lower() != vendor.lower():
                        continue
                else:
                    if device.signature.vendor != vendor:
                        continue

            if device_type and device.signature:
                if isinstance(device_type, str):
                    if device.signature.device_type.value.lower() != device_type.lower():
                        continue
                else:
                    if device.signature.device_type != device_type:
                        continue

            if status and device.status != status:
                continue

            filtered_devices.append(device)

        return filtered_devices

    def get_devices_by_vendor(self, vendor: Union[Vendor, str]) -> List[Device]:
        """Get devices by vendor."""
        return [d for d in self.devices.values()
                if d.signature and
                (d.signature.vendor == vendor if isinstance(vendor, Vendor)
                 else d.signature.vendor.value.lower() == vendor.lower())]

    def get_devices_by_type(self, device_type: Union[DeviceType, str]) -> List[Device]:
        """Get devices by type."""
        return [d for d in self.devices.values()
                if d.signature and
                (d.signature.device_type == device_type if isinstance(device_type, DeviceType)
                 else d.signature.device_type.value.lower() == device_type.lower())]

    def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics."""
        current_time = datetime.now()
        uptime_seconds = (current_time - self.stats["start_time"]).total_seconds()

        device_stats = {
            "total_devices": len(self.devices),
            "online_devices": len([d for d in self.devices.values() if d.status == DeviceStatus.ONLINE]),
            "offline_devices": len([d for d in self.devices.values() if d.status == DeviceStatus.OFFLINE]),
            "error_devices": len([d for d in self.devices.values() if d.status == DeviceStatus.ERROR]),
        }

        vendor_breakdown = {}
        type_breakdown = {}

        for device in self.devices.values():
            if device.signature:
                vendor = device.signature.vendor.value
                device_type = device.signature.device_type.value

                vendor_breakdown[vendor] = vendor_breakdown.get(vendor, 0) + 1
                type_breakdown[device_type] = type_breakdown.get(device_type, 0) + 1

        return {
            **self.stats,
            "uptime_seconds": uptime_seconds,
            "device_stats": device_stats,
            "vendor_breakdown": vendor_breakdown,
            "type_breakdown": type_breakdown,
            "success_rate": (
                self.stats["successful_collections"] / max(self.stats["total_collections"], 1)
            ) * 100
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all devices."""
        logger.info("Performing health check on all devices")

        health_results = {
            "overall_status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "device_count": len(self.devices),
            "healthy_devices": 0,
            "unhealthy_devices": 0,
            "device_details": []
        }

        # Check each device
        for device in self.devices.values():
            is_healthy = await self.snmp_engine.test_connection(device.target)

            device_health = {
                "host": device.host,
                "port": device.port,
                "status": "healthy" if is_healthy else "unhealthy",
                "response_time_ms": device.metrics.response_time_ms,
                "last_collection": device.metrics.last_collection.isoformat() if device.metrics.last_collection else None
            }

            health_results["device_details"].append(device_health)

            if is_healthy:
                health_results["healthy_devices"] += 1
            else:
                health_results["unhealthy_devices"] += 1
                if health_results["overall_status"] == "healthy":
                    health_results["overall_status"] = "degraded"

        # Set overall status based on results
        if health_results["unhealthy_devices"] == health_results["device_count"]:
            health_results["overall_status"] = "unhealthy"
        elif health_results["unhealthy_devices"] > 0:
            health_results["overall_status"] = "degraded"

        return health_results

    async def close(self):
        """Close manager and cleanup all resources."""
        logger.info("Closing SNMP Manager")

        # Close all devices
        close_tasks = [device.close() for device in self.devices.values()]
        await asyncio.gather(*close_tasks, return_exceptions=True)

        # Close components
        await self.snmp_engine.close()
        await self.scanner.close()
        await self.fingerprinter.close()

        logger.info("SNMP Manager closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()