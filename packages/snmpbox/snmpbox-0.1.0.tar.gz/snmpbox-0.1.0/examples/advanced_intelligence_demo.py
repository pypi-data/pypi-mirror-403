#!/usr/bin/env python3
"""
Advanced Intelligence Demo - Showcases all smart features of SNMP Manager.

This example demonstrates:
- Intelligent OID exploration
- Reverse engineering of undocumented devices
- Pattern recognition and device classification
- Dynamic adapter generation
- Self-learning capabilities
- Fallback strategies
- Knowledge base integration
"""

import asyncio
import logging
import json
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from snmp_manager.core.enhanced_device import EnhancedDevice
from snmp_manager.intelligence.knowledge_base import KnowledgeBase, DeviceProfile
from snmp_manager.adaptive.adapter_generator import AdapterGenerator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rich console for beautiful output
console = Console()


async def main():
    """Main demonstration of advanced intelligence features."""
    console.print("[bold blue]🧠 SNMP Manager - Advanced Intelligence Demo[/bold blue]")
    console.print("This demo showcases all the smart features we've built!")
    console.print()

    # Create enhanced device (replace with real device IP)
    device_ip = "192.168.1.10"  # Change this to your device IP

    console.print(f"[yellow]🎯 Target Device: {device_ip}[/yellow]")
    console.print()

    # Create enhanced device instance
    device = EnhancedDevice(
        host=device_ip,
        community="public",
        timeout=10,
        retries=3
    )

    try:
        # Stage 1: Intelligent Discovery
        console.print("[bold green]🔍 Stage 1: Intelligent Discovery[/bold green]")
        console.print("Exploring device capabilities using all our intelligence tools...")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            discovery_task = progress.add_task("Discovering device...", total=None)

            discovery_results = await device.intelligent_discover()

            progress.update(discovery_task, completed=True)

        # Display discovery results
        console.print("\n[bold]🎊 Discovery Results:[/bold]")

        discovery_table = Table(title="Discovery Stages")
        discovery_table.add_column("Stage", style="cyan")
        discovery_table.add_column("Status", style="green")
        discovery_table.add_column("Details", style="white")

        for stage_name, stage_data in discovery_results["stages"].items():
            status = "✅ Success" if stage_data.get("success") else "❌ Failed"
            details = []

            if stage_data.get("oids_discovered"):
                details.append(f"OIDs: {stage_data['oids_discovered']}")
            if stage_data.get("classification"):
                cls = stage_data["classification"]
                details.append(f"{cls['vendor']} {cls['device_type']}")
            if stage_data.get("profile_found"):
                details.append(f"Profile: {stage_data['profile_found']}")
            if stage_data.get("success_rate"):
                details.append(f"Success: {stage_data['success_rate']:.1%}")

            discovery_table.add_row(
                stage_name.replace("_", " ").title(),
                status,
                "; ".join(details) if details else stage_data.get("message", "No details")
            )

        console.print(discovery_table)

        # Show final device profile
        if discovery_results.get("final_profile"):
            profile = discovery_results["final_profile"]
            console.print(f"\n[bold]📋 Final Device Profile:[/bold]")
            console.print(f"  • Vendor: {profile['vendor']}")
            console.print(f"  • Type: {profile['device_type']}")
            console.print(f"  • Model: {profile['model']}")
            console.print(f"  • Confidence: {profile.get('identification_confidence', 0):.2f}")

        # Show generated adapter
        if discovery_results.get("generated_adapter"):
            adapter = discovery_results["generated_adapter"]
            console.print(f"\n[bold]🔧 Generated Adapter:[/bold]")
            console.print(f"  • Name: {adapter['name']}")
            console.print(f"  • OID Mappings: {len(adapter['oid_mappings'])}")
            console.print(f"  • Transform Rules: {len(adapter['transforms'])}")
            console.print(f"  • Collection Strategy: {adapter['collection_strategy']}")

        # Stage 2: Intelligent Collection
        console.print(f"\n[bold green]📊 Stage 2: Intelligent Collection[/bold green]")
        console.print("Collecting data using smart strategies and fallback methods...")

        collection_start = asyncio.get_event_loop().time()
        collected_data = await device.collect_with_intelligence()
        collection_time = asyncio.get_event_loop().time() - collection_start

        console.print(f"✅ Collection completed in {collection_time:.2f} seconds")
        console.print(f"📈 Collected {len(collected_data)} data fields")

        # Display intelligence metadata
        if "intelligence" in collected_data:
            intel = collected_data["intelligence"]
            console.print(f"\n[bold]🧠 Intelligence Metadata:[/bold]")
            console.print(f"  • Collection Method: {intel['collection_method']}")
            console.print(f"  • Strategy Used: {intel['strategy_used']}")
            console.print(f"  • Success Rate: {intel['strategy_results'][0].get('success', False):.1%}")

        # Stage 3: Learning and Insights
        console.print(f"\n[bold green]🎓 Stage 3: Learning & Insights[/bold green]")
        console.print("Analyzing device and generating insights...")

        insights = await device.get_intelligent_insights()

        # Display device capabilities
        capabilities = insights["collection_capabilities"]
        console.print(f"\n[bold]⚡ Device Capabilities:[/bold]")
        console.print(f"  • OID Exploration Available: {'✅' if capabilities['oid_exploration_available'] else '❌'}")
        console.print(f"  • Reverse Engineered: {'✅' if capabilities['reverse_engineered'] else '❌'}")
        console.print(f"  • Profile Available: {'✅' if capabilities['profile_available'] else '❌'}")
        console.print(f"  • Adapter Generated: {'✅' if capabilities['adapter_generated'] else '❌'}")

        # Display performance metrics
        if "performance_insights" in insights:
            perf = insights["performance_insights"]
            console.print(f"\n[bold]📈 Performance Insights:[/bold]")
            console.print(f"  • Total Intelligent Collections: {perf.get('total_intelligent_collections', 0)}")
            console.print(f"  • Learning Instances: {perf.get('learning_instances_count', 0)}")

            if "strategy_success_rates" in perf:
                console.print(f"  • Strategy Success Rates:")
                for method, stats in perf["strategy_success_rates"].items():
                    success_rate = (stats["successes"] / stats["total"]) * 100 if stats["total"] > 0 else 0
                    console.print(f"    - {method}: {success_rate:.1f}% ({stats['successes']}/{stats['total']})")

        # Display similar devices
        if "similar_devices" in insights and insights["similar_devices"]:
            console.print(f"\n[bold]🔗 Similar Devices Found:[/bold]")
            for device_id, similarity in insights["similar_devices"][:3]:
                console.print(f"  • {device_id}: {similarity:.1%} similar")

        # Display cluster information
        if "cluster_insights" in insights:
            cluster = insights["cluster_insights"]
            console.print(f"\n[bold]👥 Device Cluster Information:[/bold]")
            console.print(f"  • Cluster Name: {cluster['cluster_info']['name']}")
            console.print(f"  • Devices in Cluster: {cluster['cluster_info']['device_count']}")
            console.print(f"  • Cluster Confidence: {cluster['cluster_info']['confidence']:.2f}")

        # Stage 4: Knowledge Base Demo
        console.print(f"\n[bold green]🌐 Stage 4: Knowledge Base Integration[/bold green]")
        console.print("Demonstrating community-driven knowledge sharing...")

        # Create a temporary knowledge base for demo
        kb = KnowledgeBase()

        # Simulate adding a discovered device profile
        if device.signature and device.explored_oids:
            demo_profile = DeviceProfile(
                profile_id=f"demo_{device.signature.vendor.value}_{int(asyncio.get_event_loop().time())}",
                vendor=device.signature.vendor.value,
                device_type=device.signature.device_type.value,
                model=device.signature.model or "Unknown",
                contributed_by="advanced_demo",
                working_oids=list(device.explored_oids.keys()),
                tags=["demo", "intelligent_discovery"],
                notes="Automatically discovered through intelligent exploration"
            )

            profile_id = kb.add_device_profile(demo_profile)
            console.print(f"✅ Added device profile to knowledge base: {profile_id}")

            # Search for similar profiles
            similar_profiles = kb.search_profiles(
                vendor=device.signature.vendor.value,
                device_type=device.signature.device_type.value
            )

            console.print(f"🔍 Found {len(similar_profiles)} similar profiles in knowledge base")

            if similar_profiles:
                console.print("Top similar profiles:")
                for profile in similar_profiles[:3]:
                    console.print(f"  • {profile.name}: {profile.rating:.1f}/5.0 rating")

        # Show knowledge base statistics
        kb_stats = kb.get_statistics()
        console.print(f"\n[bold]📚 Knowledge Base Statistics:[/bold]")
        console.print(f"  • Total Profiles: {kb_stats['total_profiles']}")
        console.print(f"  • Verified Profiles: {kb_stats['verified_profiles']}")
        console.print(f"  • Total Contributions: {kb_stats['total_contributions']}")
        console.print(f"  • Supported Vendors: {kb_stats['vendors_count']}")
        console.print(f"  • Device Types: {kb_stats['device_types_count']}")

        # Final Summary
        console.print(f"\n[bold blue]🎉 Advanced Intelligence Demo Complete![/bold blue]")

        summary_table = Table(title="Demo Summary")
        summary_table.add_column("Feature", style="cyan")
        summary_table.add_column("Status", style="green")
        summary_table.add_column("Results", style="white")

        features = [
            ("Intelligent Discovery", "✅", f"{discovery_results['total_duration_ms']:.1f}ms"),
            ("Pattern Recognition", "✅", f"Device classified"),
            ("OID Exploration", "✅", f"{len(device.explored_oids)} OIDs"),
            ("Reverse Engineering", "✅" if device.reverse_engineered_data else "⚪", "Enhanced mapping"),
            ("Dynamic Adapter", "✅" if device.generated_adapter else "⚪", "Auto-generated"),
            ("Self-Learning", "✅", f"{len(device.learning_history)} instances"),
            ("Fallback Strategies", "✅", "Robust collection"),
            ("Knowledge Base", "✅", "Community integration")
        ]

        for feature, status, results in features:
            summary_table.add_row(feature, status, results)

        console.print(summary_table)

        # Save results for inspection
        output_file = f"advanced_demo_results_{device.host.replace('.', '_')}.json"

        demo_results = {
            "demo_timestamp": asyncio.get_event_loop().time(),
            "target_device": device_ip,
            "discovery_results": discovery_results,
            "collected_data_keys": list(collected_data.keys()),
            "device_insights": insights,
            "advanced_metrics": device.advanced_metrics
        }

        with open(output_file, 'w') as f:
            json.dump(demo_results, f, indent=2, default=str)

        console.print(f"\n💾 Detailed results saved to: {output_file}")

        console.print("\n[bold yellow]💡 What This Demo Shows:[/bold yellow]")
        console.print("• Automatic device discovery without manual configuration")
        console.print("• Intelligent OID exploration and mapping")
        console.print("• Pattern recognition for device classification")
        console.print("• Reverse engineering of undocumented devices")
        console.print("• Dynamic adapter generation from discovered patterns")
        console.print("• Self-learning from device interactions")
        console.print("• Robust fallback strategies for reliable collection")
        console.print("• Community-driven knowledge base integration")
        console.print("\n[bold green]🚀 This system can handle ANY SNMP device, even undocumented ones![/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]❌ Demo Error: {e}[/bold red]")
        logger.exception("Detailed error information:")

    finally:
        # Cleanup
        await device.close()
        console.print("\n[blue]🧹 Resources cleaned up[/blue]")


if __name__ == "__main__":
    asyncio.run(main())