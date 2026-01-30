"""
Unified Data Structures for SNMP Manager

This module defines the unified data structures that are used across the SNMP Manager
for consistent data representation and database storage.

These structures are designed to work with all database backends and provide
a consistent interface for device data, OLT data, and ONU data.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
import json


class DeviceStatus(Enum):
    """Device status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class ONUStatus(Enum):
    """ONU status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOS = "los"  # Loss of Signal
    LOF = "lof"  # Loss of Frame
    LOAI = "loai"  # Loss of AIS
    LOOMI = "loomi"  # Loss of OMCI
    UNKNOWN = "unknown"


class PortStatus(Enum):
    """Port status enumeration."""
    UP = "up"
    DOWN = "down"
    ADMIN_DOWN = "admin_down"
    TESTING = "testing"
    UNKNOWN = "unknown"


@dataclass
class SNMPMetrics:
    """SNMP operation metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)


@dataclass
class DeviceInfo:
    """Basic device information."""
    device_id: str
    host: str
    vendor: Optional[str] = None
    model: Optional[str] = None
    device_type: Optional[str] = None
    firmware_version: Optional[str] = None
    serial_number: Optional[str] = None
    location: Optional[str] = None
    contact: Optional[str] = None
    description: Optional[str] = None


@dataclass
class SystemInfo:
    """System information from SNMP."""
    system_description: Optional[str] = None
    system_uptime: Optional[int] = None
    system_name: Optional[str] = None
    system_location: Optional[str] = None
    system_contact: Optional[str] = None
    snmp_version: str = "2c"
    community: Optional[str] = None


@dataclass
class NetworkInterface:
    """Network interface information."""
    if_index: int
    if_name: Optional[str] = None
    if_type: Optional[int] = None
    if_speed: Optional[int] = None
    if_admin_status: Optional[PortStatus] = None
    if_oper_status: Optional[PortStatus] = None
    if_mtu: Optional[int] = None
    if_mac_address: Optional[str] = None
    if_in_octets: Optional[int] = None
    if_out_octets: Optional[int] = None
    if_in_errors: Optional[int] = None
    if_out_errors: Optional[int] = None


@dataclass
class DeviceData:
    """Unified device data structure."""
    device_id: str
    host: str
    vendor: Optional[str] = None
    model: Optional[str] = None
    device_type: Optional[str] = None
    system_description: Optional[str] = None
    system_uptime: Optional[int] = None
    system_name: Optional[str] = None
    system_location: Optional[str] = None
    snmp_version: str = "2c"
    status: DeviceStatus = DeviceStatus.UNKNOWN
    interfaces: List[NetworkInterface] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_snmp_data: Dict[str, Any] = field(default_factory=dict)
    collection_timestamp: datetime = field(default_factory=datetime.now)
    snmp_metrics: SNMPMetrics = field(default_factory=SNMPMetrics)


@dataclass
class OLTData:
    """Unified OLT data structure."""
    device_id: str
    olt_id: str
    olt_name: Optional[str] = None
    olt_model: Optional[str] = None
    vendor: Optional[str] = None
    total_onus: int = 0
    active_onus: int = 0
    inactive_onus: int = 0
    total_ports: int = 0
    total_slots: int = 0
    cpu_utilization: Optional[float] = None
    memory_utilization: Optional[float] = None
    temperature: Optional[float] = None
    optical_power_tx: Optional[float] = None
    optical_power_rx: Optional[float] = None
    status: DeviceStatus = DeviceStatus.UNKNOWN
    firmware_version: Optional[str] = None
    uptime: Optional[int] = None
    ports: List['PortData'] = field(default_factory=list)
    onus: List['ONUData'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_snmp_data: Dict[str, Any] = field(default_factory=dict)
    collection_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PortData:
    """Unified port data structure."""
    device_id: str
    port_id: int
    port_name: Optional[str] = None
    port_type: Optional[str] = None
    slot_id: Optional[int] = None
    frame_id: Optional[int] = None
    admin_status: PortStatus = PortStatus.UNKNOWN
    operational_status: PortStatus = PortStatus.UNKNOWN
    optical_power_tx: Optional[float] = None
    optical_power_rx: Optional[float] = None
    current_speed: Optional[int] = None
    max_speed: Optional[int] = None
    description: Optional[str] = None
    vlan_id: Optional[int] = None
    connected_onus: List[str] = field(default_factory=list)
    profile_name: Optional[str] = None
    distance_range: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_snmp_data: Dict[str, Any] = field(default_factory=dict)
    collection_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ONUData:
    """Unified ONU data structure."""
    device_id: str
    olt_id: str
    onu_id: str
    onu_name: Optional[str] = None
    onu_type: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    port_id: Optional[int] = None
    slot_id: Optional[int] = None
    serial_number: Optional[str] = None
    mac_address: Optional[str] = None
    status: ONUStatus = ONUStatus.UNKNOWN
    admin_state: Optional[str] = None
    operational_state: Optional[str] = None
    optical_power_rx: Optional[float] = None
    optical_power_tx: Optional[float] = None
    distance: Optional[float] = None
    temperature: Optional[float] = None
    uptime: Optional[int] = None
    firmware_version: Optional[str] = None
    description: Optional[str] = None
    profile_name: Optional[str] = None
    configured_speed: Optional[int] = None
    actual_speed: Optional[int] = None
    last_registration: Optional[datetime] = None
    last_deregistration: Optional[datetime] = None
    error_count: int = 0
    alarms: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_snmp_data: Dict[str, Any] = field(default_factory=dict)
    collection_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AlarmData:
    """Unified alarm data structure."""
    device_id: str
    alarm_id: str
    alarm_type: str
    severity: str
    description: str
    timestamp: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_time: Optional[datetime] = None
    cleared: bool = False
    cleared_time: Optional[datetime] = None
    source_component: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceData:
    """Unified performance monitoring data structure."""
    device_id: str
    metric_name: str
    metric_value: Union[int, float, str]
    unit: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    component_id: Optional[str] = None
    component_type: Optional[str] = None
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NetworkDiscoveryResult:
    """Network discovery result structure."""
    discovered_devices: List[DeviceInfo] = field(default_factory=list)
    scan_range: str = ""
    scan_timestamp: datetime = field(default_factory=datetime.now)
    scan_duration: Optional[float] = None
    total_ips_scanned: int = 0
    responsive_devices: int = 0
    snmp_devices: int = 0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectionTask:
    """Data collection task structure."""
    task_id: str
    device_id: str
    task_type: str  # 'discovery', 'monitoring', 'bulk_collection'
    schedule: Optional[str] = None  # Cron expression
    priority: int = 0
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    average_duration: Optional[float] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CollectionResult:
    """Data collection result structure."""
    task_id: str
    device_id: str
    success: bool
    start_time: datetime
    end_time: datetime
    duration: float
    data_collected: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics_collected: int = 0
    records_stored: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataConverter:
    """Utility class for converting between different data formats."""

    @staticmethod
    def to_dict(obj: Union[DeviceData, OLTData, ONUData, PortData]) -> Dict[str, Any]:
        """Convert data structure to dictionary."""
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                elif isinstance(value, Enum):
                    result[key] = value.value
                elif isinstance(value, (list, tuple)):
                    result[key] = [
                        DataConverter.to_dict(item) if hasattr(item, '__dict__') else item
                        for item in value
                    ]
                elif hasattr(value, '__dict__'):
                    result[key] = DataConverter.to_dict(value)
                else:
                    result[key] = value
            return result
        return obj

    @staticmethod
    def from_dict(data_dict: Dict[str, Any], data_type: str) -> Union[DeviceData, OLTData, ONUData, PortData]:
        """Convert dictionary to data structure."""
        type_mapping = {
            'device': DeviceData,
            'olt': OLTData,
            'onu': ONUData,
            'port': PortData
        }

        data_class = type_mapping.get(data_type.lower())
        if not data_class:
            raise ValueError(f"Unknown data type: {data_type}")

        # Convert datetime strings back to datetime objects
        processed_dict = {}
        for key, value in data_dict.items():
            if key.endswith('_timestamp') and isinstance(value, str):
                try:
                    processed_dict[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    processed_dict[key] = value
            else:
                processed_dict[key] = value

        return data_class(**processed_dict)

    @staticmethod
    def to_json(obj: Union[DeviceData, OLTData, ONUData, PortData], indent: int = 2) -> str:
        """Convert data structure to JSON string."""
        return json.dumps(DataConverter.to_dict(obj), indent=indent, default=str)

    @staticmethod
    def from_json(json_str: str, data_type: str) -> Union[DeviceData, OLTData, ONUData, PortData]:
        """Convert JSON string to data structure."""
        data_dict = json.loads(json_str)
        return DataConverter.from_dict(data_dict, data_type)


class DataValidator:
    """Utility class for validating data structures."""

    @staticmethod
    def validate_device_data(data: DeviceData) -> List[str]:
        """Validate device data and return list of errors."""
        errors = []

        if not data.device_id:
            errors.append("device_id is required")

        if not data.host:
            errors.append("host is required")

        if data.snmp_version not in ["1", "2c", "3"]:
            errors.append(f"Invalid SNMP version: {data.snmp_version}")

        if data.system_uptime is not None and data.system_uptime < 0:
            errors.append("system_uptime cannot be negative")

        return errors

    @staticmethod
    def validate_olt_data(data: OLTData) -> List[str]:
        """Validate OLT data and return list of errors."""
        errors = []

        if not data.device_id:
            errors.append("device_id is required")

        if not data.olt_id:
            errors.append("olt_id is required")

        if data.total_onus < 0:
            errors.append("total_onus cannot be negative")

        if data.active_onus < 0:
            errors.append("active_onus cannot be negative")

        if data.active_onus > data.total_onus:
            errors.append("active_onus cannot be greater than total_onus")

        if data.cpu_utilization is not None and (data.cpu_utilization < 0 or data.cpu_utilization > 100):
            errors.append("cpu_utilization must be between 0 and 100")

        if data.memory_utilization is not None and (data.memory_utilization < 0 or data.memory_utilization > 100):
            errors.append("memory_utilization must be between 0 and 100")

        return errors

    @staticmethod
    def validate_onu_data(data: ONUData) -> List[str]:
        """Validate ONU data and return list of errors."""
        errors = []

        if not data.device_id:
            errors.append("device_id is required")

        if not data.olt_id:
            errors.append("olt_id is required")

        if not data.onu_id:
            errors.append("onu_id is required")

        if data.distance is not None and data.distance < 0:
            errors.append("distance cannot be negative")

        if data.error_count < 0:
            errors.append("error_count cannot be negative")

        return errors

    @staticmethod
    def validate_port_data(data: PortData) -> List[str]:
        """Validate port data and return list of errors."""
        errors = []

        if not data.device_id:
            errors.append("device_id is required")

        if data.port_id < 0:
            errors.append("port_id cannot be negative")

        if data.current_speed is not None and data.current_speed < 0:
            errors.append("current_speed cannot be negative")

        if data.max_speed is not None and data.max_speed < 0:
            errors.append("max_speed cannot be negative")

        return errors


# Utility functions for working with data structures
def create_device_id(host: str, vendor: str = None, model: str = None) -> str:
    """Create a unique device ID from host, vendor, and model."""
    import hashlib
    identifier = f"{host}"
    if vendor:
        identifier += f"_{vendor}"
    if model:
        identifier += f"_{model}"

    return hashlib.md5(identifier.encode()).hexdigest()[:16]


def create_onu_id(olt_id: str, port_id: int, onu_number: int) -> str:
    """Create a unique ONU ID from OLT ID, port ID, and ONU number."""
    return f"{olt_id}_P{port_id:02d}_ONU{onu_number:03d}"


def create_port_id(olt_id: str, slot_id: int, port_number: int) -> str:
    """Create a unique port ID from OLT ID, slot ID, and port number."""
    return f"{olt_id}_S{slot_id:02d}_P{port_number:03d}"


def calculate_onu_optical_budget(optical_power_tx: float, optical_power_rx: float) -> float:
    """Calculate optical power budget/loss."""
    if optical_power_tx is None or optical_power_rx is None:
        return None
    return optical_power_tx - optical_power_rx


def format_uptime(timeticks: int) -> str:
    """Format timeticks to human-readable uptime."""
    if timeticks is None:
        return "Unknown"

    try:
        # Convert timeticks (hundredths of seconds) to seconds
        total_seconds = timeticks // 100

        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{days}d {hours}h {minutes}m {seconds}s"
    except:
        return f"{timeticks} timeticks"


def format_optical_power(power_dbm: float) -> str:
    """Format optical power in dBm."""
    if power_dbm is None:
        return "N/A"
    return f"{power_dbm:.2f} dBm"


def get_onu_status_priority(status: ONUStatus) -> int:
    """Get priority for ONU status (lower number = higher priority)."""
    priority_map = {
        ONUStatus.LOS: 1,
        ONUStatus.LOF: 2,
        ONUStatus.LOAI: 3,
        ONUStatus.LOOMI: 4,
        ONUStatus.INACTIVE: 5,
        ONUStatus.UNKNOWN: 6,
        ONUStatus.ACTIVE: 7
    }
    return priority_map.get(status, 99)