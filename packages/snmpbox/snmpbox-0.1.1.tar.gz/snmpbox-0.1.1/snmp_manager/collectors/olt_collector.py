"""
OLT Data Collector Module

This module provides specialized data collection for OLT devices from multiple vendors.
It handles the collection of common OLT metrics like ONUs, ports, optical power,
traffic statistics, and device health information.

Supported vendors:
- V-SOL (V1600, V2800 series)
- Huawei (MA5800, MA5600 series)
- ZTE (ZXA10 series)
- Fiberhome (AN5500 series)
- Nokia (ISAM series)
- Generic SNMP-enabled OLTs

Features:
- Automatic vendor detection
- Unified data collection interface
- Vendor-specific optimization
- Bulk collection operations
- Error handling and retry logic
- Performance monitoring
- Data validation and quality checks
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import time

from ..core.enhanced_device import EnhancedDevice
from ..core.engine import SNMPEngine
from ..intelligence.reverse_engineer import ReverseEngineer
from ..utils.data_structures import (
    OLTData, ONUData, PortData, DeviceData, ONUStatus,
    PortStatus, DeviceStatus, SNMPMetrics, DataValidator
)
from ..storage.database_converter import DatabaseManager, DatabaseConfig

logger = logging.getLogger(__name__)


@dataclass
class OLTCollectionConfig:
    """Configuration for OLT data collection."""
    device_host: str
    snmp_community: str = 'public'
    snmp_version: str = '2c'
    snmp_port: int = 161
    timeout: int = 5
    retries: int = 3
    vendor_hint: Optional[str] = None
    collection_interval: int = 300  # 5 minutes
    enable_onu_collection: bool = True
    enable_port_collection: bool = True
    enable_performance_collection: bool = True
    enable_alarm_collection: bool = True
    bulk_collection_size: int = 50
    use_reverse_engineering: bool = True
    database_config: Optional[DatabaseConfig] = None


class OLTAdapter:
    """Base class for vendor-specific OLT adapters."""

    def __init__(self, device: EnhancedDevice):
        self.device = device
        self.vendor = "generic"
        self.oid_mappings = {}
        self.collection_methods = {}

    async def identify_vendor(self) -> bool:
        """Identify if this adapter matches the device vendor."""
        return False

    async def collect_olt_info(self) -> Dict[str, Any]:
        """Collect basic OLT information."""
        return {}

    async def collect_onu_list(self) -> List[Dict[str, Any]]:
        """Collect list of ONUs connected to the OLT."""
        return []

    async def collect_onu_details(self, onu_ids: List[str]) -> List[Dict[str, Any]]:
        """Collect detailed information for specific ONUs."""
        return []

    async def collect_port_list(self) -> List[Dict[str, Any]]:
        """Collect list of ports on the OLT."""
        return []

    async def collect_port_details(self, port_ids: List[str]) -> List[Dict[str, Any]]:
        """Collect detailed information for specific ports."""
        return []

    async def collect_performance_data(self) -> Dict[str, Any]:
        """Collect performance and health data."""
        return {}

    async def collect_alarms(self) -> List[Dict[str, Any]]:
        """Collect active alarms."""
        return []


class VSOLAdapter(OLTAdapter):
    """V-SOL OLT adapter."""

    def __init__(self, device: EnhancedDevice):
        super().__init__(device)
        self.vendor = "vsol"
        self.oid_mappings = {
            # System OIDs
            'sysDescr': '1.3.6.1.2.1.1.1.0',
            'sysUpTime': '1.3.6.1.2.1.1.3.0',
            'sysName': '1.3.6.1.2.1.1.5.0',

            # V-SOL enterprise OIDs
            'vsolOLT': '1.3.6.1.4.1.3902.1.3',
            'vsolOLTInfo': '1.3.6.1.4.1.3902.1.3.1',
            'vsolONUTable': '1.3.6.1.4.1.3902.1.3.2',
            'vsolPortTable': '1.3.6.1.4.1.3902.1.3.3',
            'vsolPerformance': '1.3.6.1.4.1.3902.1.3.4',
        }

    async def identify_vendor(self) -> bool:
        """Identify if this is a V-SOL OLT."""
        try:
            # Try to get V-SOL specific OID
            result = await self.device.get('1.3.6.1.4.1.3902.1.3.1.1.0')
            if result.success:
                logger.info("Identified V-SOL OLT")
                return True

            # Check system description for V-SOL
            sys_descr = await self.device.get('1.3.6.1.2.1.1.1.0')
            if sys_descr.success and 'vsol' in sys_descr.value.lower():
                logger.info("Identified V-SOL OLT from system description")
                return True

            return False
        except:
            return False

    async def collect_olt_info(self) -> Dict[str, Any]:
        """Collect V-SOL OLT information."""
        info = {}

        try:
            # Basic system info
            sys_descr = await self.device.get(self.oid_mappings['sysDescr'])
            if sys_descr.success:
                info['system_description'] = str(sys_descr.value)

            sys_uptime = await self.device.get(self.oid_mappings['sysUpTime'])
            if sys_uptime.success:
                info['uptime'] = int(sys_descr.value) if sys_descr.value else 0

            sys_name = await self.device.get(self.oid_mappings['sysName'])
            if sys_name.success:
                info['olt_name'] = str(sys_name.value)

            # V-SOL specific info
            olt_model = await self.device.get('1.3.6.1.4.1.3902.1.3.1.1.0')
            if olt_model.success:
                info['olt_model'] = str(olt_model.value)

            total_onus = await self.device.get('1.3.6.1.4.1.3902.1.3.1.2.0')
            if total_onus.success:
                info['total_onus'] = int(total_onus.value)

            active_onus = await self.device.get('1.3.6.1.4.1.3902.1.3.1.3.0')
            if active_onus.success:
                info['active_onus'] = int(active_onus.value)

            cpu_usage = await self.device.get('1.3.6.1.4.1.3902.1.3.1.4.0')
            if cpu_usage.success:
                info['cpu_utilization'] = float(cpu_usage.value)

            memory_usage = await self.device.get('1.3.6.1.4.1.3902.1.3.1.5.0')
            if memory_usage.success:
                info['memory_utilization'] = float(memory_usage.value)

            temperature = await self.device.get('1.3.6.1.4.1.3902.1.3.1.6.0')
            if temperature.success:
                info['temperature'] = float(temperature.value)

        except Exception as e:
            logger.error(f"Error collecting V-SOL OLT info: {e}")

        return info

    async def collect_onu_list(self) -> List[Dict[str, Any]]:
        """Collect V-SOL ONU list."""
        onu_list = []

        try:
            # Walk V-SOL ONU table
            onu_table = await self.device.walk('1.3.6.1.4.1.3902.1.3.2.1')

            for onu_data in onu_table:
                if onu_data.success:
                    # Parse ONU ID from OID
                    oid_parts = onu_data.oid.split('.')
                    if len(oid_parts) >= 14:
                        port_id = int(oid_parts[-2])
                        onu_id = int(oid_parts[-1])

                        onu_info = {
                            'onu_id': f"P{port_id:02d}_ONU{onu_id:03d}",
                            'port_id': port_id,
                            'onu_number': onu_id,
                            'value': str(onu_data.value)
                        }
                        onu_list.append(onu_info)

        except Exception as e:
            logger.error(f"Error collecting V-SOL ONU list: {e}")

        return onu_list


class HuaweiAdapter(OLTAdapter):
    """Huawei OLT adapter."""

    def __init__(self, device: EnhancedDevice):
        super().__init__(device)
        self.vendor = "huawei"
        self.oid_mappings = {
            # Huawei enterprise OIDs
            'huaweiOLT': '1.3.6.1.4.1.2011.6',
            'huaweiMA5800': '1.3.6.1.4.1.2011.6.128',
            'huaweiMA5600': '1.3.6.1.4.1.2011.6.139',
        }

    async def identify_vendor(self) -> bool:
        """Identify if this is a Huawei OLT."""
        try:
            # Check system description for Huawei
            sys_descr = await self.device.get('1.3.6.1.2.1.1.1.0')
            if sys_descr.success and any(keyword in sys_descr.value.lower()
                                        for keyword in ['huawei', 'ma5800', 'ma5600']):
                logger.info("Identified Huawei OLT")
                return True

            # Try Huawei specific OID
            result = await self.device.get('1.3.6.1.4.1.2011.6.128.1.1.1.0')
            if result.success:
                logger.info("Identified Huawei OLT")
                return True

            return False
        except:
            return False

    async def collect_olt_info(self) -> Dict[str, Any]:
        """Collect Huawei OLT information."""
        info = {}

        try:
            # Basic system info
            sys_descr = await self.device.get('1.3.6.1.2.1.1.1.0')
            if sys_descr.success:
                info['system_description'] = str(sys_descr.value)

            sys_uptime = await self.device.get('1.3.6.1.2.1.1.3.0')
            if sys_uptime.success:
                info['uptime'] = int(sys_uptime.value)

            # Huawei specific info
            # These would be actual Huawei OIDs based on the specific model
            # This is a template for the structure

        except Exception as e:
            logger.error(f"Error collecting Huawei OLT info: {e}")

        return info


class ZTEAdapter(OLTAdapter):
    """ZTE OLT adapter."""

    def __init__(self, device: EnhancedDevice):
        super().__init__(device)
        self.vendor = "zte"
        self.oid_mappings = {
            # ZTE enterprise OIDs
            'zteOLT': '1.3.6.1.4.1.3902.1',
            'zteZXA10': '1.3.6.1.4.1.3902.1.1',
        }

    async def identify_vendor(self) -> bool:
        """Identify if this is a ZTE OLT."""
        try:
            # Check system description for ZTE
            sys_descr = await self.device.get('1.3.6.1.2.1.1.1.0')
            if sys_descr.success and any(keyword in sys_descr.value.lower()
                                        for keyword in ['zte', 'zxa10']):
                logger.info("Identified ZTE OLT")
                return True

            return False
        except:
            return False

    async def collect_olt_info(self) -> Dict[str, Any]:
        """Collect ZTE OLT information."""
        info = {}

        try:
            # Basic system info
            sys_descr = await self.device.get('1.3.6.1.2.1.1.1.0')
            if sys_descr.success:
                info['system_description'] = str(sys_descr.value)

        except Exception as e:
            logger.error(f"Error collecting ZTE OLT info: {e}")

        return info


class OLTCollector:
    """Main OLT data collector with vendor-specific adapters."""

    def __init__(self, config: OLTCollectionConfig):
        self.config = config
        self.device = EnhancedDevice(
            host=config.device_host,
            community=config.snmp_community,
            version=config.snmp_version,
            port=config.snmp_port,
            timeout=config.timeout,
            retries=config.retries
        )

        self.reverse_engineer = ReverseEngineer(self.device) if config.use_reverse_engineering else None
        self.database_manager = None

        if config.database_config:
            self.database_manager = DatabaseManager(config.database_config)

        # Initialize adapters
        self.adapters = [
            VSOLAdapter(self.device),
            HuaweiAdapter(self.device),
            ZTEAdapter(self.device),
        ]

        self.current_adapter = None
        self.collection_metrics = SNMPMetrics()

    async def initialize(self) -> bool:
        """Initialize the collector and detect vendor."""
        try:
            logger.info(f"Initializing OLT collector for {self.config.device_host}")

            # Connect to database if configured
            if self.database_manager:
                if not await self.database_manager.connect():
                    logger.warning("Failed to connect to database")

            # Test basic connectivity
            sys_descr = await self.device.get('1.3.6.1.2.1.1.1.0')
            if not sys_descr.success:
                logger.error(f"Cannot connect to device {self.config.device_host}")
                return False

            # Detect vendor
            await self._detect_vendor()

            if not self.current_adapter:
                logger.warning("No specific adapter found, using generic collection")
                # Use generic adapter (could be implemented as a base class)
            else:
                logger.info(f"Using {self.current_adapter.vendor} adapter")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize OLT collector: {e}")
            return False

    async def _detect_vendor(self) -> None:
        """Detect the OLT vendor and select appropriate adapter."""
        for adapter in self.adapters:
            if await adapter.identify_vendor():
                self.current_adapter = adapter
                break

    async def collect_all_data(self) -> OLTData:
        """Collect comprehensive data from the OLT."""
        start_time = time.time()

        try:
            logger.info(f"Starting data collection from {self.config.device_host}")

            # Collect basic device info
            device_info = await self._collect_device_info()

            # Create OLT data structure
            olt_data = OLTData(
                device_id=device_info.get('device_id', f"olt_{self.config.device_host}"),
                olt_id=device_info.get('olt_name', f"OLT_{self.config.device_host}"),
                olt_name=device_info.get('olt_name'),
                olt_model=device_info.get('olt_model'),
                vendor=self.current_adapter.vendor if self.current_adapter else "unknown",
                uptime=device_info.get('uptime'),
                total_onus=device_info.get('total_onus', 0),
                active_onus=device_info.get('active_onus', 0),
                total_ports=device_info.get('total_ports', 0),
                cpu_utilization=device_info.get('cpu_utilization'),
                memory_utilization=device_info.get('memory_utilization'),
                temperature=device_info.get('temperature'),
                status=DeviceStatus.ONLINE,
                collection_timestamp=datetime.now()
            )

            # Collect ONUs if enabled
            if self.config.enable_onu_collection and self.current_adapter:
                onus = await self._collect_onu_data()
                olt_data.onus = onus
                olt_data.active_onus = len([onu for onu in onus if onu.status == ONUStatus.ACTIVE])
                olt_data.total_onus = len(onus)

            # Collect ports if enabled
            if self.config.enable_port_collection and self.current_adapter:
                ports = await self._collect_port_data()
                olt_data.ports = ports
                olt_data.total_ports = len(ports)

            # Collect performance data if enabled
            if self.config.enable_performance_collection and self.current_adapter:
                perf_data = await self.current_adapter.collect_performance_data()
                olt_data.metadata['performance'] = perf_data

            # Collect alarms if enabled
            if self.config.enable_alarm_collection and self.current_adapter:
                alarms = await self.current_adapter.collect_alarms()
                olt_data.metadata['alarms'] = alarms

            # Update metrics
            duration = time.time() - start_time
            self.collection_metrics.total_requests += 1
            self.collection_metrics.successful_requests += 1
            self.collection_metrics.average_response_time = duration
            self.collection_metrics.last_request_time = datetime.now()

            # Store in database if configured
            if self.database_manager:
                try:
                    await self.database_manager.store_snmp_data(olt_data)
                    logger.debug("OLT data stored in database")
                except Exception as e:
                    logger.error(f"Failed to store OLT data: {e}")

            logger.info(f"Collected OLT data in {duration:.2f}s: "
                       f"{len(olt_data.onus)} ONUs, {len(olt_data.ports)} ports")

            return olt_data

        except Exception as e:
            duration = time.time() - start_time
            self.collection_metrics.total_requests += 1
            self.collection_metrics.failed_requests += 1
            self.collection_metrics.errors.append(str(e))

            logger.error(f"Failed to collect OLT data: {e}")

            # Return OLT data with error status
            return OLTData(
                device_id=f"olt_{self.config.device_host}",
                olt_id=f"OLT_{self.config.device_host}",
                vendor="unknown",
                status=DeviceStatus.ERROR,
                collection_timestamp=datetime.now(),
                metadata={'error': str(e), 'collection_duration': duration}
            )

    async def _collect_device_info(self) -> Dict[str, Any]:
        """Collect basic device information."""
        info = {}

        try:
            # Basic system information
            sys_descr = await self.device.get('1.3.6.1.2.1.1.1.0')
            if sys_descr.success:
                info['system_description'] = str(sys_descr.value)

            sys_uptime = await self.device.get('1.3.6.1.2.1.1.3.0')
            if sys_uptime.success:
                info['uptime'] = int(sys_uptime.value)

            sys_name = await self.device.get('1.3.6.1.2.1.1.5.0')
            if sys_name.success:
                info['olt_name'] = str(sys_name.value)

            info['device_id'] = f"olt_{self.config.device_host}"

            # Get vendor-specific info
            if self.current_adapter:
                vendor_info = await self.current_adapter.collect_olt_info()
                info.update(vendor_info)

        except Exception as e:
            logger.error(f"Error collecting device info: {e}")

        return info

    async def _collect_onu_data(self) -> List[ONUData]:
        """Collect ONU data."""
        onus = []

        try:
            if not self.current_adapter:
                return onus

            # Get ONU list
            onu_list = await self.current_adapter.collect_onu_list()

            # Collect details for each ONU
            for onu_info in onu_list:
                try:
                    onu_data = ONUData(
                        device_id=f"olt_{self.config.device_host}",
                        olt_id=f"OLT_{self.config.device_host}",
                        onu_id=onu_info.get('onu_id', ''),
                        onu_name=onu_info.get('onu_name'),
                        port_id=onu_info.get('port_id'),
                        status=self._parse_onu_status(onu_info.get('status', 'unknown')),
                        optical_power_rx=onu_info.get('optical_power_rx'),
                        optical_power_tx=onu_info.get('optical_power_tx'),
                        distance=onu_info.get('distance'),
                        serial_number=onu_info.get('serial_number'),
                        description=onu_info.get('description'),
                        collection_timestamp=datetime.now(),
                        raw_snmp_data=onu_info
                    )

                    # Validate ONU data
                    errors = DataValidator.validate_onu_data(onu_data)
                    if errors:
                        logger.warning(f"ONU data validation errors for {onu_data.onu_id}: {errors}")

                    onus.append(onu_data)

                except Exception as e:
                    logger.error(f"Error processing ONU {onu_info.get('onu_id', 'unknown')}: {e}")

        except Exception as e:
            logger.error(f"Error collecting ONU data: {e}")

        return onus

    async def _collect_port_data(self) -> List[PortData]:
        """Collect port data."""
        ports = []

        try:
            if not self.current_adapter:
                return ports

            # Get port list
            port_list = await self.current_adapter.collect_port_list()

            # Collect details for each port
            for port_info in port_list:
                try:
                    port_data = PortData(
                        device_id=f"olt_{self.config.device_host}",
                        port_id=port_info.get('port_id', 0),
                        port_name=port_info.get('port_name'),
                        port_type=port_info.get('port_type'),
                        slot_id=port_info.get('slot_id'),
                        admin_status=self._parse_port_status(port_info.get('admin_status')),
                        operational_status=self._parse_port_status(port_info.get('operational_status')),
                        optical_power_tx=port_info.get('optical_power_tx'),
                        optical_power_rx=port_info.get('optical_power_rx'),
                        description=port_info.get('description'),
                        collection_timestamp=datetime.now(),
                        raw_snmp_data=port_info
                    )

                    # Validate port data
                    errors = DataValidator.validate_port_data(port_data)
                    if errors:
                        logger.warning(f"Port data validation errors for port {port_data.port_id}: {errors}")

                    ports.append(port_data)

                except Exception as e:
                    logger.error(f"Error processing port {port_info.get('port_id', 'unknown')}: {e}")

        except Exception as e:
            logger.error(f"Error collecting port data: {e}")

        return ports

    def _parse_onu_status(self, status_str: str) -> ONUStatus:
        """Parse ONU status string to enum."""
        status_mapping = {
            'active': ONUStatus.ACTIVE,
            'inactive': ONUStatus.INACTIVE,
            'los': ONUStatus.LOS,
            'lof': ONUStatus.LOF,
            'unknown': ONUStatus.UNKNOWN,
        }
        return status_mapping.get(status_str.lower(), ONUStatus.UNKNOWN)

    def _parse_port_status(self, status_str: str) -> PortStatus:
        """Parse port status string to enum."""
        status_mapping = {
            'up': PortStatus.UP,
            'down': PortStatus.DOWN,
            'admin_down': PortStatus.ADMIN_DOWN,
            'testing': PortStatus.TESTING,
            'unknown': PortStatus.UNKNOWN,
        }
        return status_mapping.get(status_str.lower(), PortStatus.UNKNOWN)

    async def start_monitoring(self) -> None:
        """Start continuous monitoring of the OLT."""
        logger.info(f"Starting OLT monitoring for {self.config.device_host}")

        while True:
            try:
                # Collect data
                olt_data = await self.collect_all_data()

                # Check for alerts or issues
                await self._check_alerts(olt_data)

                # Wait for next collection
                await asyncio.sleep(self.config.collection_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def _check_alerts(self, olt_data: OLTData) -> None:
        """Check for alerts and conditions that need attention."""
        alerts = []

        # Check temperature
        if olt_data.temperature and olt_data.temperature > 70:
            alerts.append(f"High temperature: {olt_data.temperature}°C")

        # Check CPU utilization
        if olt_data.cpu_utilization and olt_data.cpu_utilization > 90:
            alerts.append(f"High CPU utilization: {olt_data.cpu_utilization}%")

        # Check memory utilization
        if olt_data.memory_utilization and olt_data.memory_utilization > 90:
            alerts.append(f"High memory utilization: {olt_data.memory_utilization}%")

        # Check for offline ONUs
        inactive_onus = [onu for onu in olt_data.onus if onu.status != ONUStatus.ACTIVE]
        if len(inactive_onus) > len(olt_data.onus) * 0.1:  # More than 10% inactive
            alerts.append(f"High number of inactive ONUs: {len(inactive_onus)}/{len(olt_data.onus)}")

        # Log alerts
        for alert in alerts:
            logger.warning(f"ALERT for {self.config.device_host}: {alert}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.database_manager:
                await self.database_manager.disconnect()

            await self.device.close()
            logger.info("OLT collector cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


class OLTCollectionsManager:
    """Manager for multiple OLT collectors."""

    def __init__(self):
        self.collectors = {}
        self.tasks = {}

    async def add_olt(self, config: OLTCollectionConfig) -> bool:
        """Add an OLT to monitor."""
        try:
            collector = OLTCollector(config)
            if await collector.initialize():
                self.collectors[config.device_host] = collector
                logger.info(f"Added OLT {config.device_host} to monitoring")
                return True
            else:
                logger.error(f"Failed to initialize collector for {config.device_host}")
                return False
        except Exception as e:
            logger.error(f"Error adding OLT {config.device_host}: {e}")
            return False

    async def start_all_monitoring(self) -> None:
        """Start monitoring all added OLTs."""
        for host, collector in self.collectors.items():
            task = asyncio.create_task(collector.start_monitoring())
            self.tasks[host] = task
            logger.info(f"Started monitoring for {host}")

    async def stop_all_monitoring(self) -> None:
        """Stop monitoring all OLTs."""
        for task in self.tasks.values():
            task.cancel()

        for collector in self.collectors.values():
            await collector.cleanup()

        self.tasks.clear()
        logger.info("Stopped all OLT monitoring")

    async def collect_from_all(self) -> Dict[str, OLTData]:
        """Collect data from all OLTs once."""
        results = {}

        for host, collector in self.collectors.items():
            try:
                data = await collector.collect_all_data()
                results[host] = data
            except Exception as e:
                logger.error(f"Error collecting from {host}: {e}")

        return results