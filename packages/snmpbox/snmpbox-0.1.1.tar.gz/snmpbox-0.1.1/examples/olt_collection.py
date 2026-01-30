#!/usr/bin/env python3
"""
OLT-specific data collection example.

This example shows how to collect detailed data from OLT devices
and work with vendor-specific information.
"""

import asyncio
import logging
import json
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from snmp_manager import SNMPManager
from snmp_manager.discovery.fingerprinter import Vendor, DeviceType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rich console for nice output
console = Console()


async def main():
    """Main OLT collection example."""
    console.print("[bold blue]SNMP Manager - OLT Data Collection Example[/bold blue]")
    console.print()

    # Create SNMP Manager
    async with SNMPManager() as manager:
        # Example: Add a known OLT device
        console.print("🔧 Adding OLT device...")

        # Replace with your actual OLT IP
        olt_ip = "192.168.1.10"  # Change this to your OLT IP

        try:
            device = await manager.add_device(
                host=olt_ip,
                community="public",
                timeout=10,
                retries=3
            )

            console.print(f"✅ Added device: {device.host}")
            console.print()

            # Initialize device
            console.print("🔬 Initializing device...")
            success = await device.initialize()

            if not success:
                console.print("❌ Failed to initialize device")
                return

            # Display device information
            if device.signature:
                console.print(Panel(
                    f"[bold]Device Information:[/bold]\n"
                    f"Vendor: {device.signature.vendor.value}\n"
                    f"Type: {device.signature.device_type.value}\n"
                    f"Model: {device.signature.model or 'Unknown'}\n"
                    f"Firmware: {device.signature.firmware_version or 'Unknown'}\n"
                    f"Confidence: {device.signature.confidence:.2f}",
                    title="Device Fingerprint",
                    border_style="green"
                ))

            console.print()

            # Collect detailed data
            console.print("📊 Collecting OLT data...")
            data = await device.collect()

            # Display collection summary
            if "metadata" in data:
                metadata = data["metadata"]
                console.print(Panel(
                    f"[bold]Collection Summary:[/bold]\n"
                    f"Duration: {metadata.get('collection_duration_ms', 0):.2f}ms\n"
                    f"Timestamp: {metadata.get('collection_timestamp', 'Unknown')}\n"
                    f"Method: {metadata.get('collection_method', 'Unknown')}",
                    title="Collection Metadata",
                    border_style="blue"
                ))

            # Display system information
            if "system" in data:
                console.print("\n[bold]🖥️  System Information:[/bold]")
                system_info = data["system"]

                tree = Tree("System")
                if "description" in system_info:
                    tree.add(f"Description: {system_info['description']}")
                if "name" in system_info:
                    tree.add(f"Name: {system_info['name']}")
                if "location" in system_info:
                    tree.add(f"Location: {system_info['location']}")
                if "uptime_ticks" in system_info:
                    tree.add(f"Uptime: {system_info['uptime_ticks']} timeticks")

                console.print(tree)

            # Display OLT-specific information
            if "olt_specific" in data:
                console.print("\n[bold]📡 OLT-Specific Information:[/bold]")
                olt_info = data["olt_specific"]

                for category, info in olt_info.items():
                    console.print(f"\n[green]{category.upper()}:[/green]")
                    if isinstance(info, list):
                        for item in info[:10]:  # Show first 10 items
                            console.print(f"  {item}")
                    elif isinstance(info, dict):
                        for key, value in list(info.items())[:10]:
                            console.print(f"  {key}: {value}")
                    else:
                        console.print(f"  {info}")

            # Display interfaces
            if "interfaces" in data:
                console.print("\n[bold]🔌 Interface Information:[/bold]")
                interfaces = data["interfaces"]

                if isinstance(interfaces, list):
                    console.print(f"Found {len(interfaces)} interface entries")
                    # Show first few interfaces
                    for i, interface in enumerate(interfaces[:5]):
                        if isinstance(interface, tuple) and len(interface) >= 2:
                            oid, value = interface[0], interface[1]
                            console.print(f"  Interface {i+1}: {oid} = {value}")

            # Save data to JSON file
            output_file = f"olt_data_{device.host.replace('.', '_')}.json"
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            console.print(f"\n💾 Data saved to: {output_file}")

            # Display device metrics
            console.print("\n[bold]📈 Device Metrics:[/bold]")
            metrics = device.metrics
            console.print(f"  Response Time: {metrics.response_time_ms:.2f}ms")
            console.print(f"  Successful Collections: {metrics.successful_collections}")
            console.print(f"  SNMP Errors: {metrics.snmp_errors}")
            if metrics.last_collection:
                console.print(f"  Last Collection: {metrics.last_collection}")

        except Exception as e:
            console.print(f"❌ Error: {e}")
            logger.exception("Detailed error information:")

        # Health check
        console.print("\n[bold]🏥 Performing Health Check...[/bold]")
        health = await manager.health_check()

        console.print(Panel(
            f"[bold]Overall Status:[/bold] {health['overall_status']}\n"
            f"Healthy Devices: {health['healthy_devices']}\n"
            f"Unhealthy Devices: {health['unhealthy_devices']}\n"
            f"Total Devices: {health['device_count']}",
            title="Health Check Results",
            border_style="green" if health['overall_status'] == "healthy" else "yellow"
        ))


if __name__ == "__main__":
    asyncio.run(main())