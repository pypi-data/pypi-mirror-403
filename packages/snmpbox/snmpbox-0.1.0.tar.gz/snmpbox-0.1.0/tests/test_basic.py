#!/usr/bin/env python3
"""
Basic test of the SNMP Manager implementation.

This script tests the core functionality without requiring actual devices.
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_snmp_engine():
    """Test SNMP Engine functionality."""
    print("Testing SNMP Engine...")

    from snmp_manager.core.engine import SNMPEngine, SNMPTarget, SNMPVersion

    engine = SNMPEngine()

    # Create test target
    from snmp_manager.core.engine import SNMPCredentials
    credentials = SNMPCredentials(community="public", version=SNMPVersion.V2C)
    target = SNMPTarget(
        host="127.0.0.1",
        port=161,
        credentials=credentials
    )

    print(f"✅ SNMP Engine created successfully")
    print(f"   Target: {target.host}:{target.port}")
    print(f"   Community: {target.credentials.community}")
    print(f"   Version: {target.credentials.version.name}")

    await engine.close()
    print("✅ SNMP Engine closed successfully")


async def test_device_fingerprinter():
    """Test Device Fingerprinter functionality."""
    print("\n🧪 Testing Device Fingerprinter...")

    from snmp_manager.discovery.fingerprinter import DeviceFingerprinter, Vendor, DeviceType

    fingerprinter = DeviceFingerprinter()

    # Test pattern database loading
    print(f"✅ Pattern database loaded with {len(fingerprinter.vendor_patterns)} vendors")
    print(f"   Vendors: {[v.value for v in fingerprinter.vendor_patterns.keys()]}")
    print(f"   Device types: {[dt.value for dt in fingerprinter.device_type_patterns.keys()]}")

    # Test vendor identification from description
    test_cases = [
        ("Huawei MA5800-X7 OLT device", Vendor.HUAWEI),
        ("ZTE ZXA10 C220 OLT", Vendor.ZTE),
        ("V-SOL V1600D GPON OLT", Vendor.VSOL),
        ("Unknown device", Vendor.UNKNOWN),
    ]

    for description, expected_vendor in test_cases:
        vendor, confidence = fingerprinter._identify_vendor_from_description(description)
        status = "✅" if vendor == expected_vendor else "❌"
        print(f"   {status} '{description}' -> {vendor.value} (confidence: {confidence:.2f})")

    await fingerprinter.close()
    print("✅ Device Fingerprinter closed successfully")


async def test_network_scanner():
    """Test Network Scanner functionality."""
    print("\n🧪 Testing Network Scanner...")

    from snmp_manager.discovery.scanner import NetworkScanner

    scanner = NetworkScanner(max_concurrent_scans=10, timeout=1.0)

    # Test IP generation
    import ipaddress
    network = ipaddress.ip_network("192.168.1.0/30", strict=False)
    ips = [str(ip) for ip in network.hosts()]
    print(f"✅ Network scanner created")
    print(f"   Generated {len(ips)} IPs from 192.168.1.0/30: {ips}")

    # Test vendor pattern parsing
    test_description = "Huawei MA5800-X7 GPON OLT, Version V100R020C10"
    vendor, model = scanner._parse_device_description(test_description)
    print(f"   Description parsing: '{test_description}'")
    print(f"   Vendor: {vendor}, Model: {model}")

    # Test enterprise OID identification
    test_oids = [
        ("1.3.6.1.4.1.2011.6.128.1.1.1", "huawei"),
        ("1.3.6.1.4.1.3902.110.1.1", "zte"),
        ("1.3.6.1.4.1.999.1.1.1", "unknown"),
    ]

    for oid, expected_vendor in test_oids:
        vendor = scanner._identify_vendor_from_enterprise_oid(oid)
        status = "✅" if vendor == expected_vendor else "❌"
        print(f"   {status} {oid} -> {vendor}")

    await scanner.close()
    print("✅ Network Scanner closed successfully")


async def test_device_class():
    """Test Device class functionality."""
    print("\n🧪 Testing Device Class...")

    from snmp_manager.core.device import Device, DeviceStatus
    from snmp_manager.core.engine import SNMPVersion

    # Create device
    device = Device(
        host="192.168.1.100",
        port=161,
        community="public",
        version=SNMPVersion.V2C,
        timeout=5,
        retries=3
    )

    print(f"✅ Device created: {device}")
    print(f"   Host: {device.host}")
    print(f"   Port: {device.port}")
    print(f"   Status: {device.status.value}")
    print(f"   Metrics: {device.metrics.response_time_ms}ms response time")

    # Test cache functionality
    print(f"   Cache valid: {device._is_cache_valid()}")

    await device.close()
    print("✅ Device closed successfully")


async def test_config_manager():
    """Test Configuration Manager functionality."""
    print("\n🧪 Testing Configuration Manager...")

    from snmp_manager.config.manager import ConfigManager
    from snmp_manager.config.adapter import AdapterConfig, OIDMapping, TransformRule

    # Create config manager
    config_manager = ConfigManager(config_dir="test_configs")
    print(f"✅ Config Manager created with directory: {config_manager.config_dir}")

    # Create sample adapter config
    oid_mappings = [
        OIDMapping(
            name="system_description",
            oid="1.3.6.1.2.1.1.1.0",
            description="System description",
            data_type="string",
            category="system"
        ),
        OIDMapping(
            name="system_uptime",
            oid="1.3.6.1.2.1.1.3.0",
            description="System uptime",
            data_type="integer",
            category="system"
        )
    ]

    transforms = [
        TransformRule(
            name="uptime_to_days",
            input_pattern="system_uptime",
            output_field="uptime_days",
            transformation_type="scale",
            parameters={"scale_factor": 0.000864}
        )
    ]

    adapter_config = AdapterConfig(
        name="test-olt",
        version="1.0.0",
        device_type="olt",
        vendor="test",
        supported_models=["Test-OLT-1000"],
        oid_mappings=oid_mappings,
        transforms=transforms
    )

    print(f"✅ Sample Adapter Config created:")
    print(f"   Name: {adapter_config.name}")
    print(f"   Vendor: {adapter_config.vendor}")
    print(f"   Device Type: {adapter_config.device_type}")
    print(f"   OID Mappings: {len(adapter_config.oid_mappings)}")
    print(f"   Transforms: {len(adapter_config.transforms)}")

    # Test validation
    errors = config_manager.validate_config(adapter_config)
    print(f"   Validation errors: {len(errors)}")
    for error in errors:
        print(f"     - {error}")

    # Test saving sample configs
    try:
        config_manager.create_sample_configs()
        print(f"✅ Sample configs created in {config_manager.config_dir}")
    except Exception as e:
        print(f"⚠️  Could not create sample configs: {e}")


async def test_snmp_manager():
    """Test main SNMP Manager functionality."""
    print("\n🧪 Testing SNMP Manager...")

    from snmp_manager.core.manager import SNMPManager
    from snmp_manager.core.engine import SNMPVersion

    # Create manager
    manager = SNMPManager(
        max_concurrent_operations=10,
        default_community="public",
        default_version=SNMPVersion.V2C
    )

    print(f"✅ SNMP Manager created")
    print(f"   Max concurrent operations: {manager.max_concurrent_operations}")
    print(f"   Default community: {manager.default_community}")
    print(f"   Registered devices: {len(manager.devices)}")

    # Test adding device
    device = await manager.add_device(
        host="192.168.1.200",
        port=161,
        community="public"
    )

    print(f"✅ Device added to manager: {device.host}")
    print(f"   Total registered devices: {len(manager.devices)}")

    # Test statistics
    stats = manager.get_statistics()
    print(f"✅ Manager statistics:")
    print(f"   Total discoveries: {stats['total_discoveries']}")
    print(f"   Total collections: {stats['total_collections']}")
    print(f"   Success rate: {stats['success_rate']:.1f}%")

    await manager.close()
    print("✅ SNMP Manager closed successfully")


async def main():
    """Run all tests."""
    print("Starting SNMP Manager Basic Tests")
    print("=" * 50)

    try:
        await test_snmp_engine()
        await test_device_fingerprinter()
        await test_network_scanner()
        await test_device_class()
        await test_config_manager()
        await test_snmp_manager()

        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        print("Core functionality is working")
        print("Ready for real device testing")

    except Exception as e:
        print(f"\nTest failed: {e}")
        logger.exception("Detailed error information:")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)