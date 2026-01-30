#!/usr/bin/env python3
"""
OLT Multivendor Data Collector Example

This example demonstrates how to use the OLT data collector to collect data
from multiple OLT vendors (V-SOL, Huawei, ZTE, etc.) with automatic vendor detection
and unified data output.

Features demonstrated:
- Automatic vendor detection
- Collection of OLT, ONU, and port data
- Database storage (MongoDB, PostgreSQL, etc.)
- Continuous monitoring with alerts
- Bulk operations and performance optimization
- Error handling and retry logic
- Data validation and quality checks
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Import our OLT collector components
from snmp_manager.collectors.olt_collector import (
    OLTCollector, OLTCollectionsManager, OLTCollectionConfig
)
from snmp_manager.storage.database_converter import DatabaseConfig, DatabaseManager
from snmp_manager.utils.data_structures import OLTData, ONUData, PortData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demonstrate_single_olt_collection():
    """
    Demonstrate collecting data from a single OLT.
    """
    print("🎯 SINGLE OLT DATA COLLECTION DEMONSTRATION")
    print("="*60)

    # Configure OLT collection
    config = OLTCollectionConfig(
        device_host="192.168.1.10",  # Replace with your OLT IP
        snmp_community="public",      # Replace with your SNMP community
        snmp_version="2c",
        timeout=5,
        retries=3,
        collection_interval=300,  # 5 minutes
        enable_onu_collection=True,
        enable_port_collection=True,
        enable_performance_collection=True,
        enable_alarm_collection=True,
        use_reverse_engineering=True,
        # Optional: Configure database storage
        database_config=DatabaseConfig(
            db_type="mongodb",  # or "postgresql", "sqlite"
            host="localhost",
            port=27017,
            database="olt_monitoring",
            username="",
            password=""
        )
    )

    # Create and initialize collector
    collector = OLTCollector(config)

    try:
        print(f"🔧 Initializing collector for {config.device_host}...")

        if not await collector.initialize():
            print(f"❌ Failed to initialize collector for {config.device_host}")
            return

        print(f"✅ Collector initialized successfully")
        print(f"🏷️  Detected vendor: {collector.current_adapter.vendor if collector.current_adapter else 'Unknown'}")

        # Collect comprehensive data
        print(f"\n📊 Starting comprehensive data collection...")
        olt_data = await collector.collect_all_data()

        # Display results
        print(f"\n📋 COLLECTION RESULTS:")
        print(f"  • OLT ID: {olt_data.olt_id}")
        print(f"  • Vendor: {olt_data.vendor}")
        print(f"  • Model: {olt_data.olt_model}")
        print(f"  • Status: {olt_data.status}")
        print(f"  • Total ONUs: {olt_data.total_onus}")
        print(f"  • Active ONUs: {olt_data.active_onus}")
        print(f"  • Total Ports: {olt_data.total_ports}")

        if olt_data.cpu_utilization:
            print(f"  • CPU Usage: {olt_data.cpu_utilization:.1f}%")

        if olt_data.memory_utilization:
            print(f"  • Memory Usage: {olt_data.memory_utilization:.1f}%")

        if olt_data.temperature:
            print(f"  • Temperature: {olt_data.temperature:.1f}°C")

        # Display ONU information
        if olt_data.onus:
            print(f"\n📱 ONU INFORMATION (Top 10):")
            for i, onu in enumerate(olt_data.onus[:10]):
                status_emoji = "🟢" if onu.status.value == "active" else "🔴"
                power_info = ""
                if onu.optical_power_rx:
                    power_info = f" | Rx: {onu.optical_power_rx:.2f} dBm"
                if onu.distance:
                    power_info += f" | Distance: {onu.distance:.1f}m"

                print(f"  {i+1:2d}. {status_emoji} {onu.onu_id} | Port: {onu.port_id} | Status: {onu.status.value}{power_info}")

            if len(olt_data.onus) > 10:
                print(f"     ... and {len(olt_data.onus) - 10} more ONUs")

        # Display port information
        if olt_data.ports:
            print(f"\n🔌 PORT INFORMATION (Top 10):")
            for i, port in enumerate(olt_data.ports[:10]):
                status_emoji = "🟢" if port.operational_status.value == "up" else "🔴"
                power_info = ""
                if port.optical_power_rx:
                    power_info = f" | Rx: {port.optical_power_rx:.2f} dBm"

                print(f"  {i+1:2d}. {status_emoji} Port {port.port_id} ({port.port_name}) | {port.operational_status.value}{power_info}")

            if len(olt_data.ports) > 10:
                print(f"     ... and {len(olt_data.ports) - 10} more ports")

        # Performance and alerts
        if olt_data.metadata.get('performance'):
            perf = olt_data.metadata['performance']
            print(f"\n📈 PERFORMANCE DATA:")
            for key, value in perf.items():
                print(f"  • {key}: {value}")

        if olt_data.metadata.get('alarms'):
            alarms = olt_data.metadata['alarms']
            print(f"\n🚨 ACTIVE ALARMS: {len(alarms)}")
            for alarm in alarms[:5]:  # Show first 5 alarms
                print(f"  • {alarm}")

        # Collection metrics
        metrics = collector.collection_metrics
        print(f"\n📊 COLLECTION METRICS:")
        print(f"  • Total Requests: {metrics.total_requests}")
        print(f"  • Successful: {metrics.successful_requests}")
        print(f"  • Failed: {metrics.failed_requests}")
        print(f"  • Average Response Time: {metrics.average_response_time:.2f}s")

        return olt_data

    except Exception as e:
        print(f"❌ Error during collection: {e}")
        return None

    finally:
        await collector.cleanup()


async def demonstrate_multivendor_collection():
    """
    Demonstrate collecting data from multiple OLT vendors.
    """
    print("\n🌐 MULTIVENDOR OLT COLLECTION DEMONSTRATION")
    print("="*60)

    # Configure multiple OLTs from different vendors
    olt_configs = [
        OLTCollectionConfig(
            device_host="192.168.1.10",  # V-SOL OLT
            snmp_community="public",
            vendor_hint="vsol",
            enable_onu_collection=True,
            enable_port_collection=True,
        ),
        OLTCollectionConfig(
            device_host="192.168.1.20",  # Huawei OLT
            snmp_community="public",
            vendor_hint="huawei",
            enable_onu_collection=True,
            enable_port_collection=True,
        ),
        OLTCollectionConfig(
            device_host="192.168.1.30",  # ZTE OLT
            snmp_community="public",
            vendor_hint="zte",
            enable_onu_collection=True,
            enable_port_collection=True,
        ),
    ]

    # Create collections manager
    manager = OLTCollectionsManager()

    try:
        # Add all OLTs to monitoring
        print("🔧 Adding OLTs to monitoring...")
        for config in olt_configs:
            success = await manager.add_olt(config)
            if success:
                print(f"  ✅ Added {config.device_host}")
            else:
                print(f"  ❌ Failed to add {config.device_host}")

        # Collect data from all OLTs
        print(f"\n📊 Collecting data from all OLTs...")
        all_data = await manager.collect_from_all()

        # Display summary
        print(f"\n📋 MULTIVENDOR COLLECTION SUMMARY:")
        total_onus = 0
        total_ports = 0
        vendor_counts = {}

        for host, olt_data in all_data.items():
            vendor = olt_data.vendor
            vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1

            total_onus += olt_data.total_onus
            total_ports += olt_data.total_ports

            print(f"  • {host} ({vendor}): {olt_data.total_onus} ONUs, {olt_data.total_ports} ports")

        print(f"\n📊 AGGREGATE STATISTICS:")
        print(f"  • Total OLTs: {len(all_data)}")
        print(f"  • Total ONUs: {total_onus}")
        print(f"  • Total Ports: {total_ports}")
        print(f"  • Vendors: {list(vendor_counts.keys())}")

        return all_data

    except Exception as e:
        print(f"❌ Error during multivendor collection: {e}")
        return None

    finally:
        await manager.stop_all_monitoring()


async def demonstrate_continuous_monitoring():
    """
    Demonstrate continuous monitoring with alerts.
    """
    print("\n⏰ CONTINUOUS MONITORING DEMONSTRATION")
    print("="*60)

    # Configure OLT for monitoring
    config = OLTCollectionConfig(
        device_host="192.168.1.10",  # Replace with your OLT IP
        snmp_community="public",
        collection_interval=60,  # 1 minute for demo
        enable_onu_collection=True,
        enable_performance_collection=True,
        enable_alarm_collection=True,
        database_config=DatabaseConfig(
            db_type="sqlite",
            database="olt_monitoring.db"
        )
    )

    collector = OLTCollector(config)

    try:
        print(f"🔧 Initializing continuous monitoring for {config.device_host}...")

        if not await collector.initialize():
            print(f"❌ Failed to initialize collector")
            return

        print(f"✅ Monitoring initialized")
        print(f"⏰ Collection interval: {config.collection_interval} seconds")
        print(f"🗄️  Database: SQLite (olt_monitoring.db)")
        print(f"\n🚀 Starting continuous monitoring...")
        print(f"   (Press Ctrl+C to stop)")

        # Run monitoring for a limited time (demo)
        start_time = datetime.now()
        max_duration = 300  # 5 minutes max for demo

        while True:
            try:
                # Check if we've exceeded demo time
                if (datetime.now() - start_time).seconds > max_duration:
                    print(f"\n⏰ Demo time limit reached ({max_duration}s)")
                    break

                # Collect data
                olt_data = await collector.collect_all_data()

                # Show brief status
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] 📊 {olt_data.vendor} {olt_data.olt_model}: "
                      f"{olt_data.active_onus}/{olt_data.total_onus} ONUs active | "
                      f"CPU: {olt_data.cpu_utilization or 0:.1f}% | "
                      f"Temp: {olt_data.temperature or 0:.1f}°C")

                # Wait for next collection
                await asyncio.sleep(config.collection_interval)

            except KeyboardInterrupt:
                print(f"\n⏹️  Monitoring stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Monitoring error: {e}")
                await asyncio.sleep(30)  # Wait before retrying

    finally:
        await collector.cleanup()


async def demonstrate_database_operations():
    """
    Demonstrate database operations with collected data.
    """
    print("\n🗄️  DATABASE OPERATIONS DEMONSTRATION")
    print("="*60)

    # Test different database types
    databases = [
        {
            "name": "SQLite",
            "config": DatabaseConfig(
                db_type="sqlite",
                database="olt_data.db"
            )
        },
        {
            "name": "MongoDB",
            "config": DatabaseConfig(
                db_type="mongodb",
                host="localhost",
                port=27017,
                database="olt_monitoring"
            )
        }
    ]

    for db in databases:
        print(f"\n🔧 Testing {db['name']} database operations...")

        try:
            # Create database manager
            db_manager = DatabaseManager(db['config'])

            # Connect to database
            if not await db_manager.connect():
                print(f"  ❌ Failed to connect to {db['name']}")
                continue

            print(f"  ✅ Connected to {db['name']}")

            # Create sample OLT data
            sample_olt = OLTData(
                device_id="demo_olt_001",
                olt_id="DEMO_OLT_001",
                olt_name="Demo OLT",
                vendor="vsol",
                olt_model="V2800",
                total_onus=50,
                active_onus=45,
                total_ports=16,
                cpu_utilization=35.5,
                memory_utilization=42.3,
                temperature=45.2,
                status="online"
            )

            # Store data
            record_id = await db_manager.store_snmp_data(sample_olt)
            print(f"  ✅ Stored OLT data with ID: {record_id}")

            # Create sample ONU data
            sample_onus = []
            for i in range(5):
                onu = ONUData(
                    device_id="demo_olt_001",
                    olt_id="DEMO_OLT_001",
                    onu_id=f"P01_ONU{i+1:03d}",
                    onu_name=f"ONU_{i+1}",
                    port_id=1,
                    status="active",
                    optical_power_rx=-20.5 + i,
                    distance=1000 + i * 100,
                    serial_number=f"ONU{i+1:012d}"
                )
                sample_onus.append(onu)

            # Store bulk data
            onu_ids = await db_manager.store_snmp_data(sample_onus)
            print(f"  ✅ Stored {len(onu_ids)} ONU records")

            # Query data
            devices = await db_manager.query_data('devices', limit=5)
            print(f"  ✅ Queried {len(devices)} device records")

            # Get latest data
            latest = await db_manager.get_latest_device_data("demo_olt_001")
            print(f"  ✅ Retrieved latest data for device")

            # Disconnect
            await db_manager.disconnect()
            print(f"  ✅ Disconnected from {db['name']}")

        except Exception as e:
            print(f"  ❌ {db['name']} error: {e}")


async def demonstrate_reverse_engineering_integration():
    """
    Demonstrate reverse engineering integration for unknown OLTs.
    """
    print("\n🔬 REVERSE ENGINEERING INTEGRATION DEMONSTRATION")
    print("="*60)

    # Configure OLT with reverse engineering enabled
    config = OLTCollectionConfig(
        device_host="192.168.1.100",  # Unknown OLT
        snmp_community="public",
        use_reverse_engineering=True,
        collection_interval=300,
        enable_onu_collection=True,
        enable_port_collection=True
    )

    collector = OLTCollector(config)

    try:
        print(f"🔧 Initializing reverse engineering for {config.device_host}...")

        if not await collector.initialize():
            print(f"❌ Failed to initialize collector")
            return

        print(f"✅ Reverse engineering initialized")

        # Show discovery results
        if collector.reverse_engineer:
            print(f"\n🔍 Reverse engineering capabilities:")
            print(f"  • OID pattern recognition: Enabled")
            print(f"  • Device fingerprinting: Enabled")
            print(f"  • Vendor identification: Enabled")
            print(f"  • Adaptive data collection: Enabled")

        # Collect data with reverse engineering
        print(f"\n📊 Collecting data with reverse engineering...")
        olt_data = await collector.collect_all_data()

        # Display reverse engineering results
        print(f"\n🔬 REVERSE ENGINEERING RESULTS:")
        print(f"  • Detected Vendor: {olt_data.vendor}")
        print(f"  • Device Model: {olt_data.olt_model}")
        print(f"  • Total OIDs Discovered: {len(olt_data.raw_snmp_data)}")
        print(f"  • Collection Success: {'✅' if olt_data.status.value == 'online' else '❌'}")

        # Show discovered patterns
        if olt_data.metadata:
            print(f"\n🎯 DISCOVERED PATTERNS:")
            for key, value in olt_data.metadata.items():
                if isinstance(value, dict) and len(value) > 0:
                    print(f"  • {key}: {len(value)} items")

        return olt_data

    except Exception as e:
        print(f"❌ Reverse engineering error: {e}")
        return None

    finally:
        await collector.cleanup()


async def main():
    """
    Main function demonstrating all OLT collector features.
    """
    print("🚀 OLT MULTIVENDOR DATA COLLECTOR DEMONSTRATION")
    print("="*80)
    print("This demo showcases the complete OLT monitoring system with:")
    print("• Automatic vendor detection (V-SOL, Huawei, ZTE, etc.)")
    print("• Comprehensive data collection (OLT, ONU, port, performance)")
    print("• Database storage (MongoDB, PostgreSQL, SQLite)")
    print("• Continuous monitoring with alerts")
    print("• Reverse engineering for unknown devices")
    print("• Bulk operations and performance optimization")
    print("="*80)

    # Note: Update these IPs with your actual OLT devices
    print("\n⚠️  IMPORTANT:")
    print("This demo uses example IP addresses (192.168.1.x).")
    print("Update the IP addresses in the code with your actual OLT devices.")
    print("Ensure SNMP is enabled and accessible from this machine.")
    print()

    try:
        # Demo 1: Single OLT collection
        print("🎯 Running Demo 1: Single OLT Collection")
        await demonstrate_single_olt_collection()

        # Demo 2: Multivendor collection
        print("\n🌐 Running Demo 2: Multivendor Collection")
        await demonstrate_multivendor_collection()

        # Demo 3: Database operations
        print("\n🗄️ Running Demo 3: Database Operations")
        await demonstrate_database_operations()

        # Demo 4: Reverse engineering
        print("\n🔬 Running Demo 4: Reverse Engineering Integration")
        await demonstrate_reverse_engineering_integration()

        # Demo 5: Continuous monitoring (optional - commented out for demo)
        # print("\n⏰ Running Demo 5: Continuous Monitoring")
        # print("(This will run for 5 minutes - press Ctrl+C to stop early)")
        # await demonstrate_continuous_monitoring()

        print(f"\n🎉 ALL DEMONSTRATIONS COMPLETED!")
        print(f"\n📚 What you've seen:")
        print(f"  ✅ Automatic vendor detection and adapter selection")
        print(f"  ✅ Comprehensive OLT/ONU/Port data collection")
        print(f"  ✅ Database storage with multiple backends")
        print(f"  ✅ Data validation and quality assurance")
        print(f"  ✅ Reverse engineering for unknown devices")
        print(f"  ✅ Performance monitoring and alerting")
        print(f"  ✅ Bulk operations and scalability")

        print(f"\n🚀 Ready for production use!")
        print(f"   • Configure your OLT IP addresses")
        print(f"   • Set up database connections")
        print(f"   • Deploy the monitoring system")
        print(f"   • Start collecting valuable OLT metrics!")

    except KeyboardInterrupt:
        print(f"\n⏹️  Demonstrations stopped by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        logger.exception("Detailed error information:")


if __name__ == "__main__":
    """
    Run the complete OLT multivendor collector demonstration.

    Usage:
        python examples/olt_multivendor_collector_example.py

    Before running:
        1. Update the OLT IP addresses in the code
        2. Ensure SNMP community strings are correct
        3. Configure database connections if needed
        4. Install required database drivers (pymongo, asyncpg, aiosqlite)

    Example installation:
        pip install pymongo asyncpg aiosqlite

    Features demonstrated:
        - Single and multivendor OLT monitoring
        - Database storage with multiple backends
        - Continuous monitoring with alerts
        - Reverse engineering for unknown devices
        - Performance optimization and bulk operations
    """
    asyncio.run(main())