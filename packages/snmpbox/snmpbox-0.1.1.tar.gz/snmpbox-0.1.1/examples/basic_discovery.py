#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic device discovery example.

This example shows how to use SNMP Manager to discover devices on a network
and collect basic information from them.
"""

import asyncio
import logging
import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, 'strict')

from rich.console import Console
from rich.table import Table

from snmp_manager import SNMPManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rich console for nice output
console = Console(force_terminal=True)


async def main():
    """Main discovery example."""
    console.print("[bold blue]SNMP Manager - Network Discovery Example[/bold blue]")
    console.print()

    # Create SNMP Manager
    async with SNMPManager() as manager:
        # Discover devices on local network
        console.print("🔍 Discovering devices on local network...")
        discovered_devices = await manager.discover_local_network()

        if not discovered_devices:
            console.print("⚠️  No SNMP devices found on local network")
            console.print("💡 Try specifying a network range, e.g. 192.168.1.0/24")
            return

        console.print(f"✅ Found {len(discovered_devices)} SNMP devices!")
        console.print()

        # Display discovered devices in a table
        table = Table(title="Discovered Devices")
        table.add_column("IP Address", style="cyan")
        table.add_column("Port", style="magenta")
        table.add_column("Community", style="green")
        table.add_column("Status", style="yellow")

        for device in discovered_devices:
            status = "🟢 Online" if device.status.value == "online" else "🔴 Offline"
            table.add_row(
                device.host,
                str(device.port),
                device.target.credentials.community,
                status
            )

        console.print(table)
        console.print()

        # Initialize and fingerprint devices
        console.print("🔬 Fingerprinting devices...")
        for device in discovered_devices:
            try:
                success = await device.initialize()
                if success and device.signature:
                    console.print(
                        f"  📱 {device.host}: "
                        f"{device.signature.vendor.value} "
                        f"{device.signature.device_type.value} "
                        f"(confidence: {device.signature.confidence:.2f})"
                    )
                    if device.signature.model:
                        console.print(f"     Model: {device.signature.model}")
                else:
                    console.print(f"  ❌ {device.host}: Fingerprinting failed")
            except Exception as e:
                console.print(f"  ❌ {device.host}: Error - {e}")

        console.print()

        # Collect data from one device as example
        if discovered_devices:
            console.print("📊 Collecting data from first device...")
            try:
                data = await discovered_devices[0].collect()
                console.print(f"✅ Collection successful!")
                console.print()

                # Display basic system info
                if "system" in data:
                    console.print("[bold]System Information:[/bold]")
                    system_info = data["system"]
                    if "description" in system_info:
                        console.print(f"  Description: {system_info['description']}")
                    if "name" in system_info:
                        console.print(f"  Name: {system_info['name']}")
                    if "uptime_ticks" in system_info:
                        console.print(f"  Uptime: {system_info['uptime_ticks']} timeticks")

                # Display device identification
                if "identification" in data:
                    console.print("[bold]Device Identification:[/bold]")
                    ident = data["identification"]
                    console.print(f"  Vendor: {ident.get('vendor', 'Unknown')}")
                    console.print(f"  Type: {ident.get('device_type', 'Unknown')}")
                    console.print(f"  Model: {ident.get('model', 'Unknown')}")

                # Display metadata
                if "metadata" in data:
                    console.print("[bold]Collection Metadata:[/bold]")
                    metadata = data["metadata"]
                    console.print(f"  Duration: {metadata.get('collection_duration_ms', 0):.2f}ms")
                    console.print(f"  Timestamp: {metadata.get('collection_timestamp', 'Unknown')}")

            except Exception as e:
                console.print(f"❌ Data collection failed: {e}")

        # Display manager statistics
        console.print()
        console.print("[bold]📈 Manager Statistics:[/bold]")
        stats = manager.get_statistics()
        console.print(f"  Total devices: {stats['device_stats']['total_devices']}")
        console.print(f"  Online devices: {stats['device_stats']['online_devices']}")
        console.print(f"  Success rate: {stats['success_rate']:.1f}%")
        console.print(f"  Uptime: {stats['uptime_seconds']:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())