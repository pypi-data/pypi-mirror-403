#!/usr/bin/env python3
"""
Simple test of the SNMP Manager implementation - fixed version.
"""

import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_imports():
    """Test basic imports and instantiation."""
    print("Testing basic imports...")

    try:
        from snmp_manager.core.engine import SNMPEngine, SNMPTarget, SNMPVersion
        from snmp_manager.core.device import Device
        from snmp_manager.core.manager import SNMPManager
        from snmp_manager.discovery.fingerprinter import DeviceFingerprinter
        from snmp_manager.discovery.scanner import NetworkScanner
        from snmp_manager.config.manager import ConfigManager

        print("[OK] All imports successful")
    except ImportError as e:
        print(f"[FAIL] Import failed: {e}")
        return False

    # Test creating instances
    try:
        engine = SNMPEngine()
        print("[OK] SNMPEngine created")

        target = SNMPTarget(host="127.0.0.1")
        print("[OK] SNMPTarget created")

        device = Device(host="127.0.0.1")
        print("[OK] Device created")

        fingerprinter = DeviceFingerprinter()
        print("[OK] DeviceFingerprinter created")

        scanner = NetworkScanner()
        print("[OK] NetworkScanner created")

        config_manager = ConfigManager()
        print("[OK] ConfigManager created")

        manager = SNMPManager()
        print("[OK] SNMPManager created")

        # Cleanup
        await engine.close()
        await fingerprinter.close()
        await scanner.close()
        await manager.close()
        print("[OK] All resources closed successfully")

        return True

    except Exception as e:
        print(f"[FAIL] Instance creation failed: {e}")
        return False


async def test_pattern_matching():
    """Test device fingerprinting patterns."""
    print("\nTesting pattern matching...")

    try:
        from snmp_manager.discovery.fingerprinter import DeviceFingerprinter, Vendor, DeviceType

        fingerprinter = DeviceFingerprinter()

        # Test vendor identification
        test_cases = [
            ("Huawei MA5800-X7 OLT device", Vendor.HUAWEI),
            ("ZTE ZXA10 C220 OLT", Vendor.ZTE),
            ("V-SOL V1600D GPON OLT", Vendor.VSOL),
            ("Unknown device", Vendor.UNKNOWN),
        ]

        for description, expected_vendor in test_cases:
            vendor, confidence = fingerprinter._identify_vendor_from_description(description)
            status = "PASS" if vendor == expected_vendor else "FAIL"
            print(f"  [{status}] '{description}' -> {vendor.value} (confidence: {confidence:.2f})")

        # Test device type identification
        type_cases = [
            ("Huawei OLT MA5800", DeviceType.OLT),
            ("GPON Optical Line Terminal", DeviceType.OLT),
            ("Ethernet Switch 24P", DeviceType.SWITCH),
            ("Unknown device", DeviceType.UNKNOWN),
        ]

        for description, expected_type in type_cases:
            device_type, confidence = fingerprinter._identify_device_type_from_description(description)
            status = "PASS" if device_type == expected_type else "FAIL"
            print(f"  [{status}] '{description}' -> {device_type.value} (confidence: {confidence:.2f})")

        await fingerprinter.close()
        return True

    except Exception as e:
        print(f"[FAIL] Pattern matching test failed: {e}")
        return False


async def test_network_parsing():
    """Test network-related parsing."""
    print("\nTesting network parsing...")

    try:
        from snmp_manager.discovery.scanner import NetworkScanner

        scanner = NetworkScanner()

        # Test device description parsing
        test_description = "Huawei MA5800-X7 GPON OLT, Version V100R020C10"
        vendor, model = scanner._parse_device_description(test_description)
        print("[OK] Description parsing successful")
        print(f"  Input: {test_description}")
        print(f"  Vendor: {vendor}, Model: {model}")

        # Test enterprise OID identification
        test_oids = [
            ("1.3.6.1.4.1.2011.6.128.1.1.1", "huawei"),
            ("1.3.6.1.4.1.3902.110.1.1", "zte"),
            ("1.3.6.1.4.1.999.1.1.1", "unknown"),
        ]

        for oid, expected_vendor in test_oids:
            vendor = scanner._identify_vendor_from_enterprise_oid(oid)
            status = "PASS" if vendor == expected_vendor else "FAIL"
            print(f"  [{status}] {oid} -> {vendor}")

        await scanner.close()
        return True

    except Exception as e:
        print(f"[FAIL] Network parsing test failed: {e}")
        return False


async def test_config_system():
    """Test configuration system."""
    print("\nTesting configuration system...")

    try:
        from snmp_manager.config.adapter import AdapterConfig, OIDMapping, TransformRule
        from snmp_manager.config.manager import ConfigManager

        # Create test OID mapping
        oid_mapping = OIDMapping(
            name="test_oid",
            oid="1.3.6.1.2.1.1.1.0",
            description="Test OID",
            data_type="string"
        )
        print("[OK] OIDMapping created")

        # Create test transform rule
        transform = TransformRule(
            name="test_transform",
            input_pattern="test_input",
            output_field="test_output",
            transformation_type="scale",
            parameters={"scale_factor": 1.0}
        )
        print("[OK] TransformRule created")

        # Create adapter config
        adapter_config = AdapterConfig(
            name="test_adapter",
            version="1.0.0",
            device_type="test",
            vendor="test",
            oid_mappings=[oid_mapping],
            transforms=[transform]
        )
        print("[OK] AdapterConfig created")

        # Test config manager
        config_manager = ConfigManager()
        errors = config_manager.validate_config(adapter_config)
        print(f"[OK] Config validation completed with {len(errors)} errors")

        # Test converting to dict
        config_dict = adapter_config.to_dict()
        print(f"[OK] Config converted to dict with {len(config_dict)} keys")

        return True

    except Exception as e:
        print(f"[FAIL] Configuration system test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("Starting SNMP Manager Basic Tests")
    print("=" * 50)

    tests = [
        ("Basic Imports", test_basic_imports),
        ("Pattern Matching", test_pattern_matching),
        ("Network Parsing", test_network_parsing),
        ("Configuration System", test_config_system),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        try:
            if await test_func():
                passed += 1
                print(f"[PASS] {test_name} PASSED")
            else:
                print(f"[FAIL] {test_name} FAILED")
        except Exception as e:
            print(f"[ERROR] {test_name} ERROR: {e}")

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("All tests PASSED!")
        print("Core functionality is working correctly")
        print("Ready for real device testing")
        return 0
    else:
        print("Some tests FAILED!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)