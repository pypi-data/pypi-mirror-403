#!/usr/bin/env python3
"""
Network scanning example.

This example shows how to scan a network range for SNMP-enabled devices
and collect information from them.
"""

import asyncio
import logging
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from snmp_manager import SNMPManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rich console for nice output
console = Console()


async def main():
    """Main network scanning example."""
    console.print("[bold blue]SNMP Manager - Network Scanning Example[/bold blue]")
    console.print()

    # Get network range from user or use default
    network_range = "192.168.1.0/24"  # Change this to your network range
    console.print(f"🔍 Scanning network range: [cyan]{network_range}[/cyan]")
    console.print("⚠️  This may take a while depending on network size...")
    console.print()

    # Create SNMP Manager
    async with SNMPManager(max_concurrent_operations=100) as manager:
        # Scan network with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            scan_task = progress.add_task("Scanning network...", total=None)

            try:
                discovered_devices = await manager.discover_devices(
                    network_range=network_range,
                    communities=["public", "private", "community"],
                    ports=[161, 162]
                )

                progress.update(scan_task, completed=True)

            except Exception as e:
                console.print(f"❌ Network scan failed: {e}")
                return

        if not discovered_devices:
            console.print("⚠️  No SNMP devices found on the network")
            console.print("💡 Possible reasons:")
            console.print("   - No SNMP-enabled devices on the network")
            console.print("   - Devices use non-standard SNMP communities")
            console.print("   - Firewall blocking SNMP traffic")
            console.print("   - Network range incorrect")
            return

        console.print(f"✅ Found {len(discovered_devices)} SNMP devices!")
        console.print()

        # Display discovered devices
        table = Table(title="Discovered SNMP Devices")
        table.add_column("IP Address", style="cyan", no_wrap=True)
        table.add_column("Port", style="magenta")
        table.add_column("Community", style="green")
        table.add_column("Vendor", style="yellow")
        table.add_column("Type", style="blue")
        table.add_column("Status", style="white")

        # Initialize and fingerprint all devices
        console.print("🔬 Fingerprinting devices...")
        with Progress(console=console) as progress:
            fingerprint_task = progress.add_task("Fingerprinting...", total=len(discovered_devices))

            for device in discovered_devices:
                try:
                    await device.initialize()
                    progress.advance(fingerprint_task)
                except Exception as e:
                    logger.debug(f"Fingerprinting failed for {device.host}: {e}")
                    progress.advance(fingerprint_task)

        # Add devices to table
        for device in discovered_devices:
            status = "🟢" if device.status.value == "online" else "🔴"
            vendor = device.signature.vendor.value if device.signature else "Unknown"
            device_type = device.signature.device_type.value if device.signature else "Unknown"

            table.add_row(
                device.host,
                str(device.port),
                device.target.credentials.community,
                vendor,
                device_type,
                status
            )

        console.print(table)
        console.print()

        # Collect data from all devices
        console.print("📊 Collecting data from all devices...")
        with Progress(console=console) as progress:
            collection_task = progress.add_task("Collecting data...", total=len(discovered_devices))

            all_data = []
            for device in discovered_devices:
                try:
                    data = await device.collect()
                    all_data.append(data)
                    progress.advance(collection_task)
                except Exception as e:
                    logger.debug(f"Collection failed for {device.host}: {e}")
                    progress.advance(collection_task)

        console.print(f"✅ Collected data from {len(all_data)} devices!")
        console.print()

        # Display summary statistics
        console.print("[bold]📈 Collection Summary:[/bold]")
        stats = manager.get_statistics()

        # Vendor breakdown
        console.print("\n[green]Vendor Breakdown:[/green]")
        vendor_stats = stats.get("vendor_breakdown", {})
        for vendor, count in vendor_stats.items():
            console.print(f"  {vendor}: {count} devices")

        # Device type breakdown
        console.print("\n[blue]Device Type Breakdown:[/blue]")
        type_stats = stats.get("type_breakdown", {})
        for device_type, count in type_stats.items():
            console.print(f"  {device_type}: {count} devices")

        # Performance metrics
        console.print(f"\n[yellow]Performance Metrics:[/yellow]")
        console.print(f"  Success Rate: {stats['success_rate']:.1f}%")
        console.print(f"  Total Collections: {stats['total_collections']}")
        console.print(f"  Successful: {stats['successful_collections']}")
        console.print(f"  Failed: {stats['failed_collections']}")

        # Find most interesting devices
        console.print("\n[bold]🎯 Most Interesting Devices:[/bold]")

        # Device with most interfaces
        max_interfaces = 0
        most_connected_device = None

        for data in all_data:
            if "interfaces" in data and isinstance(data["interfaces"], list):
                interface_count = len(data["interfaces"])
                if interface_count > max_interfaces:
                    max_interfaces = interface_count
                    identification = data.get("identification", {})
                    most_connected_device = identification.get("device_id", "Unknown")

        if most_connected_device:
            console.print(f"  🌐 Most connected: {most_connected_device} ({max_interfaces} interfaces)")

        # OLT devices
        olt_count = len([d for d in all_data
                        if d.get("identification", {}).get("device_type") == "olt"])
        if olt_count > 0:
            console.print(f"  📡 OLT devices found: {olt_count}")

        # Save all data to files
        console.print(f"\n💾 Saving data files...")
        for i, data in enumerate(all_data):
            identification = data.get("identification", {})
            device_id = identification.get("device_id", f"device_{i}")
            filename = f"device_data_{device_id.replace(':', '_')}.json"

            try:
                with open(filename, 'w') as f:
                    import json
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                console.print(f"  ❌ Failed to save {filename}: {e}")

        console.print(f"✅ Saved {len(all_data)} data files")

        # Final health check
        console.print(f"\n[bold]🏥 Final Health Check:[/bold]")
        health = await manager.health_check()

        health_color = "green" if health["overall_status"] == "healthy" else "yellow"
        console.print(f"  Overall Status: [{health_color}]{health['overall_status']}[/{health_color}]")
        console.print(f"  Healthy: {health['healthy_devices']}/{health['device_count']}")


if __name__ == "__main__":
    asyncio.run(main())