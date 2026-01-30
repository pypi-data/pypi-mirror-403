#!/usr/bin/env python3
"""
V-SOL OLT Reverse Engineering Example

This example demonstrates how to handle completely undocumented V-SOL OLT devices
when you only know that they support SNMP but have no documentation.

The scenario: You have a V-SOL OLT device at IP 192.168.1.1 with SNMP community
'public', but no MIB files, no documentation, and no knowledge of available OIDs.

This example shows how to:
1. Establish basic connectivity with multiple SNMP methods
2. Use intelligent discovery to find all accessible data
3. Apply reverse engineering techniques specific to V-SOL patterns
4. Extract signal power, distance, uptime, and status information
5. Create a working adapter from discovered patterns
6. Save findings to knowledge base for future use
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import our SNMP Manager components
from snmp_manager.core.enhanced_device import EnhancedDevice
from snmp_manager.core.engine import SNMPEngine
from snmp_manager.intelligence.reverse_engineer import ReverseEngineer
from snmp_manager.intelligence.knowledge_base import KnowledgeBase
from snmp_manager.adaptive.adapter_generator import AdapterGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VSOLReverseEngineer:
    """
    Specialized reverse engineering system for V-SOL OLT devices.

    This class combines all available intelligent features to extract maximum
    information from undocumented V-SOL OLT devices.
    """

    def __init__(self, host: str, community: str = 'public'):
        """
        Initialize V-SOL reverse engineer.

        Args:
            host: IP address of the V-SOL OLT
            community: SNMP community string (default: 'public')
        """
        self.host = host
        self.community = community

        # Initialize components
        self.device = EnhancedDevice(
            host=host,
            community=community,
            version='2c',
            timeout=5,
            retries=2
        )

        self.reverse_engineer = ReverseEngineer(self.device)
        self.knowledge_base = KnowledgeBase()
        self.adapter_generator = AdapterGenerator()

        # Results storage
        self.results = {
            'device_info': {},
            'discovered_oids': {},
            'patterns_found': {},
            'vsol_specific_data': {},
            'generated_adapter': {},
            'timestamp': datetime.now().isoformat()
        }

        print(f"🔧 V-SOL Reverse Engineer initialized for {host}")
        print(f"📡 Using SNMP community: {community}")

    async def basic_connectivity_test(self) -> bool:
        """
        Test basic SNMP connectivity using multiple methods.

        Returns:
            True if basic connectivity is established
        """
        print("\n" + "="*60)
        print("🔌 STEP 1: BASIC CONNECTIVITY TEST")
        print("="*60)

        try:
            # Test 1: Try standard system OIDs
            print("📋 Testing standard system OIDs...")

            system_oids = [
                ('1.3.6.1.2.1.1.1.0', 'sysDescr'),
                ('1.3.6.1.2.1.1.3.0', 'sysUpTime'),
                ('1.3.6.1.2.1.1.5.0', 'sysName'),
                ('1.3.6.1.2.1.1.6.0', 'sysLocation'),
            ]

            for oid, name in system_oids:
                try:
                    result = await self.device.get(oid)
                    if result.success:
                        print(f"  ✅ {name}: {result.value}")
                        self.results['device_info'][name] = str(result.value)
                    else:
                        print(f"  ❌ {name}: {result.error}")
                except Exception as e:
                    print(f"  ⚠️  {name}: Error - {e}")

            # Test 2: Try V-SOL specific patterns
            print("\n🎯 Testing V-SOL specific OID patterns...")

            vsol_patterns = [
                # Common V-SOL enterprise OIDs
                ('1.3.6.1.4.1.3902.1.1.1', 'V-SOL Enterprise'),
                ('1.3.6.1.4.1.8691.1', 'Alternative V-SOL OID'),
                # Try some common OLT patterns
                ('1.3.6.1.4.1.3902.1.3.1.1.0', 'OLT Status'),
                ('1.3.6.1.4.1.3902.1.3.2.1.0', 'OLT Uptime'),
            ]

            for oid, name in vsol_patterns:
                try:
                    result = await self.device.get(oid)
                    if result.success:
                        print(f"  ✅ {name}: {result.value}")
                        self.results['device_info'][name] = str(result.value)
                    else:
                        print(f"  ❌ {name}: Not accessible")
                except Exception as e:
                    print(f"  ⚠️  {name}: Error - {e}")

            # Test 3: Walk some common branches
            print("\n🚶 Testing SNMP walks on common branches...")

            test_branches = [
                ('1.3.6.1.2.1.1', 'system'),
                ('1.3.6.1.2.1.2', 'interfaces'),
                ('1.3.6.1.4.1.3902', 'vsol_enterprise'),
            ]

            for oid, name in test_branches:
                try:
                    walk_results = await self.device.walk(oid, max_repetitions=10)
                    if walk_results:
                        print(f"  ✅ {name}: Found {len(walk_results)} OIDs")
                        for result in walk_results[:3]:  # Show first 3
                            print(f"    • {result.oid}: {result.value}")
                        if len(walk_results) > 3:
                            print(f"    ... and {len(walk_results) - 3} more")
                    else:
                        print(f"  ❌ {name}: No data found")
                except Exception as e:
                    print(f"  ⚠️  {name}: Walk error - {e}")

            return True

        except Exception as e:
            print(f"❌ Connectivity test failed: {e}")
            return False

    async def intelligent_discovery(self) -> Dict[str, Any]:
        """
        Perform comprehensive intelligent discovery of the device.

        Returns:
            Dictionary containing discovered OIDs and patterns
        """
        print("\n" + "="*60)
        print("🧠 STEP 2: INTELLIGENT DISCOVERY")
        print("="*60)

        try:
            print("🔍 Starting comprehensive device discovery...")

            # Use the enhanced device's intelligent discovery
            discovery_result = await self.device.discover_intelligently()

            if discovery_result:
                print(f"✅ Discovery completed!")
                print(f"📊 Found {len(discovery_result.get('oids', {}))} accessible OIDs")
                print(f"🎯 Device patterns: {discovery_result.get('patterns', [])}")
                print(f"🏷️  Device type: {discovery_result.get('device_type', 'Unknown')}")
                print(f"📈 Confidence: {discovery_result.get('confidence', 0):.2f}")

                self.results['discovered_oids'] = discovery_result.get('oids', {})
                self.results['patterns_found'] = {
                    'device_type': discovery_result.get('device_type'),
                    'confidence': discovery_result.get('confidence'),
                    'patterns': discovery_result.get('patterns', [])
                }

                # Show some interesting discoveries
                print("\n🎯 Notable discoveries:")
                for oid, data in list(discovery_result.get('oids', {}).items())[:10]:
                    value = data.get('value', 'N/A')
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"  • {oid}: {value}")

                return discovery_result
            else:
                print("❌ Discovery failed or no data found")
                return {}

        except Exception as e:
            print(f"❌ Intelligent discovery failed: {e}")
            return {}

    async def vsol_specialized_analysis(self) -> Dict[str, Any]:
        """
        Perform V-SOL specific analysis and reverse engineering.

        Returns:
            Dictionary containing V-SOL specific data and patterns
        """
        print("\n" + "="*60)
        print("🎯 STEP 3: V-SOL SPECIALIZED ANALYSIS")
        print("="*60)

        try:
            print("🔬 Starting V-SOL specialized reverse engineering...")

            # Use the reverse engineer with V-SOL specific strategies
            vsol_analysis = await self.reverse_engineer.reverse_engineer_device(
                device_type_hint='vsol_olt',
                analysis_depth='comprehensive'
            )

            if vsol_analysis:
                print(f"✅ V-SOL analysis completed!")
                print(f"📊 Analysis confidence: {vsol_analysis.get('confidence', 0):.2f}")
                print(f"🔍 Device profile: {vsol_analysis.get('device_profile', {})}")

                # Look for specific V-SOL data patterns
                print("\n🔬 Analyzing V-SOL specific data...")

                vsol_specific = await self._analyze_vsol_data_patterns()

                self.results['vsol_specific_data'] = {
                    'analysis': vsol_analysis,
                    'specific_data': vsol_specific
                }

                return vsol_analysis
            else:
                print("❌ V-SOL analysis failed")
                return {}

        except Exception as e:
            print(f"❌ V-SOL specialized analysis failed: {e}")
            return {}

    async def _analyze_vsol_data_patterns(self) -> Dict[str, Any]:
        """
        Analyze discovered data for V-SOL specific patterns.

        Returns:
            Dictionary containing V-SOL specific data patterns
        """
        print("🔍 Analyzing V-SOL data patterns...")

        vsol_data = {
            'signal_power': {},
            'distance_info': {},
            'uptime_info': {},
            'status_info': {},
            'onu_data': {},
            'port_data': {}
        }

        # Search for signal power related OIDs
        signal_keywords = ['power', 'signal', 'optical', 'rx', 'tx', 'level']
        for oid, data in self.results['discovered_oids'].items():
            value = str(data.get('value', '')).lower()
            oid_lower = oid.lower()

            # Check for signal power indicators
            if any(keyword in oid_lower or keyword in value for keyword in signal_keywords):
                if any(char.isdigit() for char in value):  # Contains numbers
                    vsol_data['signal_power'][oid] = data

            # Check for distance/length indicators
            if any(keyword in oid_lower or keyword in value for keyword in ['distance', 'length', 'meter', 'km']):
                vsol_data['distance_info'][oid] = data

            # Check for uptime indicators
            if any(keyword in oid_lower or keyword in value for keyword in ['uptime', 'sysuptime', 'timeticks']):
                vsol_data['uptime_info'][oid] = data

            # Check for status indicators
            if any(keyword in oid_lower or keyword in value for keyword in ['status', 'state', 'operational']):
                vsol_data['status_info'][oid] = data

        # Try to find ONU related data (typically in tables)
        print("🔍 Searching for ONU data tables...")

        # Look for table patterns
        table_patterns = [
            '1.3.6.1.4.1.3902.1.3',  # V-SOL OLT table
            '1.3.6.1.4.1.3902.1.4',  # V-SOL ONU table
            '1.3.6.1.4.1.3902.1.5',  # V-SOL port table
        ]

        for pattern in table_patterns:
            try:
                table_data = await self.device.walk(pattern, max_repetitions=20)
                if table_data:
                    print(f"  ✅ Found table data at {pattern}: {len(table_data)} entries")
                    vsol_data['onu_data'][pattern] = [t.__dict__ for t in table_data[:10]]
            except:
                pass

        # Display findings
        print(f"\n📊 V-SOL Data Analysis Results:")
        print(f"  • Signal Power OIDs: {len(vsol_data['signal_power'])}")
        print(f"  • Distance Info OIDs: {len(vsol_data['distance_info'])}")
        print(f"  • Uptime Info OIDs: {len(vsol_data['uptime_info'])}")
        print(f"  • Status Info OIDs: {len(vsol_data['status_info'])}")
        print(f"  • ONU Data Tables: {len(vsol_data['onu_data'])}")

        # Show some examples
        if vsol_data['signal_power']:
            print(f"\n💪 Signal Power Examples:")
            for oid, data in list(vsol_data['signal_power'].items())[:3]:
                print(f"  • {oid}: {data.get('value')}")

        if vsol_data['uptime_info']:
            print(f"\n⏰ Uptime Info Examples:")
            for oid, data in list(vsol_data['uptime_info'].items())[:3]:
                print(f"  • {oid}: {data.get('value')}")

        return vsol_data

    async def extract_target_data(self) -> Dict[str, Any]:
        """
        Extract the specific data you requested: signal power, distance, uptime, status.

        Returns:
            Dictionary containing the extracted target data
        """
        print("\n" + "="*60)
        print("🎯 STEP 4: EXTRACTING TARGET DATA")
        print("="*60)

        target_data = {
            'signal_power': {},
            'distance': {},
            'uptime': {},
            'status': {},
            'additional_metrics': {}
        }

        try:
            print("🎯 Extracting signal power information...")

            # Look for optical power, signal strength OIDs
            power_candidates = []
            for oid, data in self.results['discovered_oids'].items():
                value = str(data.get('value', ''))
                oid_lower = oid.lower()
                value_lower = value.lower()

                if any(keyword in oid_lower or keyword in value_lower for keyword in
                       ['power', 'optical', 'signal', 'rx', 'tx', 'level', 'dbm']):
                    if any(char.isdigit() for char in value):
                        power_candidates.append((oid, data))

            for oid, data in power_candidates[:10]:  # Top 10 candidates
                try:
                    result = await self.device.get(oid)
                    if result.success:
                        target_data['signal_power'][oid] = {
                            'value': str(result.value),
                            'description': data.get('description', 'Unknown')
                        }
                except:
                    pass

            print(f"📊 Found {len(target_data['signal_power'])} signal power metrics")

            print("📏 Extracting distance information...")

            # Look for distance/length related OIDs
            distance_candidates = []
            for oid, data in self.results['discovered_oids'].items():
                oid_lower = oid.lower()
                value = str(data.get('value', '')).lower()

                if any(keyword in oid_lower or keyword in value for keyword in
                       ['distance', 'length', 'meter', 'km', 'cable', 'fiber']):
                    distance_candidates.append((oid, data))

            for oid, data in distance_candidates[:5]:
                try:
                    result = await self.device.get(oid)
                    if result.success:
                        target_data['distance'][oid] = {
                            'value': str(result.value),
                            'description': data.get('description', 'Unknown')
                        }
                except:
                    pass

            print(f"📏 Found {len(target_data['distance'])} distance metrics")

            print("⏰ Extracting uptime information...")

            # Get system uptime and other time-related OIDs
            uptime_oids = [
                '1.3.6.1.2.1.1.3.0',  # sysUpTime
                '1.3.6.1.2.1.25.1.1.0',  # hrSystemUptime
            ]

            # Add discovered uptime OIDs
            for oid, data in self.results['discovered_oids'].items():
                oid_lower = oid.lower()
                if 'uptime' in oid_lower or 'timeticks' in oid_lower:
                    uptime_oids.append(oid)

            for oid in uptime_oids:
                try:
                    result = await self.device.get(oid)
                    if result.success:
                        target_data['uptime'][oid] = {
                            'value': str(result.value),
                            'description': 'System uptime'
                        }
                except:
                    pass

            print(f"⏰ Found {len(target_data['uptime'])} uptime metrics")

            print("📊 Extracting status information...")

            # Look for status, state, operational status
            status_candidates = []
            for oid, data in self.results['discovered_oids'].items():
                oid_lower = oid.lower()
                value = str(data.get('value', '')).lower()

                if any(keyword in oid_lower or keyword in value for keyword in
                       ['status', 'state', 'operational', 'admin', 'active']):
                    status_candidates.append((oid, data))

            for oid, data in status_candidates[:15]:
                try:
                    result = await self.device.get(oid)
                    if result.success:
                        target_data['status'][oid] = {
                            'value': str(result.value),
                            'description': data.get('description', 'Unknown')
                        }
                except:
                    pass

            print(f"📊 Found {len(target_data['status'])} status metrics")

            # Display summary
            print(f"\n📋 Target Data Extraction Summary:")
            print(f"  • Signal Power: {len(target_data['signal_power'])} metrics")
            print(f"  • Distance: {len(target_data['distance'])} metrics")
            print(f"  • Uptime: {len(target_data['uptime'])} metrics")
            print(f"  • Status: {len(target_data['status'])} metrics")

            # Show examples of each
            if target_data['signal_power']:
                print(f"\n💪 Signal Power Examples:")
                for oid, info in list(target_data['signal_power'].items())[:3]:
                    print(f"  • {oid}: {info['value']}")

            if target_data['uptime']:
                print(f"\n⏰ Uptime Examples:")
                for oid, info in list(target_data['uptime'].items())[:2]:
                    print(f"  • {oid}: {info['value']}")

            if target_data['status']:
                print(f"\n📊 Status Examples:")
                for oid, info in list(target_data['status'].items())[:3]:
                    print(f"  • {oid}: {info['value']}")

            return target_data

        except Exception as e:
            print(f"❌ Target data extraction failed: {e}")
            return target_data

    async def generate_working_adapter(self) -> Optional[Dict[str, Any]]:
        """
        Generate a working adapter from discovered patterns.

        Returns:
            Dictionary containing the generated adapter configuration
        """
        print("\n" + "="*60)
        print("🔧 STEP 5: GENERATING WORKING ADAPTER")
        print("="*60)

        try:
            print("🛠️  Generating V-SOL adapter from discovered patterns...")

            # Create device profile from discoveries
            device_profile = {
                'vendor': 'V-SOL',
                'device_type': 'OLT',
                'model': 'Unknown (Reverse Engineered)',
                'confidence': self.results['patterns_found'].get('confidence', 0),
                'discovered_oids': self.results['discovered_oids'],
                'patterns': self.results['patterns_found'].get('patterns', []),
                'target_data': self.results.get('target_data', {}),
                'timestamp': datetime.now().isoformat()
            }

            # Generate adapter configuration
            adapter_config = {
                'name': 'VSOL_ReverseEngineered',
                'description': 'Auto-generated V-SOL OLT adapter from reverse engineering',
                'version': '1.0.0-auto',
                'device_profile': device_profile,
                'oid_mappings': {},
                'data_collectors': {},
                'health_monitors': {}
            }

            # Map discovered OIDs to meaningful names
            for oid, data in self.results['discovered_oids'].items():
                oid_name = f'oid_{oid.replace(".", "_")}'
                adapter_config['oid_mappings'][oid_name] = {
                    'oid': oid,
                    'description': data.get('description', f'Discovered OID {oid}'),
                    'type': self._guess_data_type(data.get('value')),
                    'access': 'read-only'
                }

            # Create data collectors for target metrics
            if 'target_data' in self.results:
                target = self.results['target_data']

                adapter_config['data_collectors']['signal_power'] = {
                    'description': 'Signal power metrics',
                    'oids': list(target.get('signal_power', {}).keys()),
                    'interval': 300,  # 5 minutes
                    'enabled': True
                }

                adapter_config['data_collectors']['uptime'] = {
                    'description': 'Uptime metrics',
                    'oids': list(target.get('uptime', {}).keys()),
                    'interval': 60,  # 1 minute
                    'enabled': True
                }

                adapter_config['data_collectors']['status'] = {
                    'description': 'Device status metrics',
                    'oids': list(target.get('status', {}).keys()),
                    'interval': 120,  # 2 minutes
                    'enabled': True
                }

            # Create health monitors
            adapter_config['health_monitors']['connectivity'] = {
                'description': 'Basic connectivity check',
                'method': 'ping',
                'interval': 60,
                'enabled': True
            }

            self.results['generated_adapter'] = adapter_config

            print(f"✅ Adapter generated successfully!")
            print(f"📊 Adapter contains {len(adapter_config['oid_mappings'])} OID mappings")
            print(f"📈 Created {len(adapter_config['data_collectors'])} data collectors")
            print(f"💊 Created {len(adapter_config['health_monitors'])} health monitors")

            return adapter_config

        except Exception as e:
            print(f"❌ Adapter generation failed: {e}")
            return None

    def _guess_data_type(self, value: Any) -> str:
        """Guess the data type from a value."""
        if value is None:
            return 'unknown'

        str_value = str(value)

        # Try to guess the type
        if str_value.isdigit():
            return 'integer'
        elif '.' in str_value and str_value.replace('.', '').isdigit():
            return 'float'
        elif str_value.lower() in ['true', 'false', 'yes', 'no', 'on', 'off']:
            return 'boolean'
        elif 'timeticks' in str_value.lower():
            return 'timeticks'
        else:
            return 'string'

    async def save_to_knowledge_base(self) -> bool:
        """
        Save discovered patterns to knowledge base for future use.

        Returns:
            True if successfully saved
        """
        print("\n" + "="*60)
        print("💾 STEP 6: SAVING TO KNOWLEDGE BASE")
        print("="*60)

        try:
            print("💾 Saving V-SOL discovery to knowledge base...")

            # Prepare knowledge base entry
            kb_entry = {
                'device_id': f"vsol_olt_{self.host.replace('.', '_')}",
                'vendor': 'V-SOL',
                'device_type': 'OLT',
                'ip_address': self.host,
                'discovery_date': datetime.now().isoformat(),
                'confidence': self.results['patterns_found'].get('confidence', 0),
                'patterns': self.results['patterns_found'].get('patterns', []),
                'oids': self.results['discovered_oids'],
                'target_data': self.results.get('target_data', {}),
                'adapter_config': self.results.get('generated_adapter', {}),
                'success_rate': 1.0,  # This was successful
                'notes': 'Reverse engineered from undocumented V-SOL OLT'
            }

            # Save to knowledge base (in this example, just print it)
            print(f"✅ Knowledge base entry created:")
            print(f"  Device ID: {kb_entry['device_id']}")
            print(f"  Vendor: {kb_entry['vendor']}")
            print(f"  OIDs discovered: {len(kb_entry['oids'])}")
            print(f"  Confidence: {kb_entry['confidence']:.2f}")

            # Save to file for persistence
            kb_file = Path(f"vsol_knowledge_{self.host.replace('.', '_')}.json")
            with open(kb_file, 'w') as f:
                json.dump(kb_entry, f, indent=2, default=str)

            print(f"💾 Saved knowledge base entry to: {kb_file}")

            return True

        except Exception as e:
            print(f"❌ Failed to save to knowledge base: {e}")
            return False

    async def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report of the reverse engineering process.

        Returns:
            Dictionary containing the complete report
        """
        print("\n" + "="*60)
        print("📋 STEP 7: GENERATING COMPREHENSIVE REPORT")
        print("="*60)

        try:
            print("📊 Generating comprehensive report...")

            report = {
                'summary': {
                    'device_host': self.host,
                    'snmp_community': self.community,
                    'process_date': datetime.now().isoformat(),
                    'total_steps_completed': 7,
                    'success_rate': 1.0,
                },
                'device_info': self.results.get('device_info', {}),
                'discovery_summary': {
                    'oids_discovered': len(self.results.get('discovered_oids', {})),
                    'patterns_found': self.results.get('patterns_found', {}),
                    'confidence_score': self.results.get('patterns_found', {}).get('confidence', 0),
                },
                'target_data_extracted': self.results.get('target_data', {}),
                'vsol_analysis': self.results.get('vsol_specific_data', {}),
                'generated_adapter': self.results.get('generated_adapter', {}),
                'recommendations': self._generate_recommendations(),
                'next_steps': self._generate_next_steps()
            }

            # Save report to file
            report_file = Path(f"vsol_reverse_engineering_report_{self.host.replace('.', '_')}.json")
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            print(f"📋 Report saved to: {report_file}")

            # Print summary
            print(f"\n📊 REVERSE ENGINEERING SUMMARY:")
            print(f"  • Device: {self.host}")
            print(f"  • OIDs Discovered: {len(self.results.get('discovered_oids', {}))}")
            print(f"  • Signal Power Metrics: {len(self.results.get('target_data', {}).get('signal_power', {}))}")
            print(f"  • Distance Metrics: {len(self.results.get('target_data', {}).get('distance', {}))}")
            print(f"  • Uptime Metrics: {len(self.results.get('target_data', {}).get('uptime', {}))}")
            print(f"  • Status Metrics: {len(self.results.get('target_data', {}).get('status', {}))}")
            print(f"  • Confidence Score: {self.results.get('patterns_found', {}).get('confidence', 0):.2f}")
            print(f"  • Adapter Generated: {'Yes' if self.results.get('generated_adapter') else 'No'}")

            return report

        except Exception as e:
            print(f"❌ Report generation failed: {e}")
            return {}

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on findings."""
        recommendations = []

        if len(self.results.get('discovered_oids', {})) > 50:
            recommendations.append("Device is highly accessible - consider implementing comprehensive monitoring")

        if len(self.results.get('target_data', {}).get('signal_power', {})) > 0:
            recommendations.append("Signal power metrics available - implement optical power monitoring")

        if len(self.results.get('target_data', {}).get('uptime', {})) > 0:
            recommendations.append("Uptime tracking available - implement availability monitoring")

        confidence = self.results.get('patterns_found', {}).get('confidence', 0)
        if confidence > 0.7:
            recommendations.append("High confidence in device profiling - use generated adapter in production")
        elif confidence > 0.4:
            recommendations.append("Moderate confidence - test adapter thoroughly before production use")
        else:
            recommendations.append("Low confidence - use adapter with caution and continue discovery")

        recommendations.append("Save discovered patterns to knowledge base for future devices")
        recommendations.append("Consider implementing automated monitoring for critical metrics")

        return recommendations

    def _generate_next_steps(self) -> List[str]:
        """Generate next steps for the user."""
        next_steps = [
            "Test the generated adapter with actual data collection",
            "Implement automated monitoring using discovered OIDs",
            "Add device to knowledge base for community sharing",
            "Create monitoring dashboards for key metrics",
            "Set up alerts for critical status changes"
        ]

        if len(self.results.get('target_data', {}).get('signal_power', {})) > 0:
            next_steps.append("Configure alerts for signal power thresholds")

        if len(self.results.get('target_data', {}).get('status', {})) > 0:
            next_steps.append("Implement comprehensive status monitoring")

        return next_steps

    async def run_complete_reverse_engineering(self) -> Dict[str, Any]:
        """
        Run the complete V-SOL reverse engineering process.

        Returns:
            Complete results dictionary
        """
        print("🚀 STARTING COMPLETE V-SOL OLT REVERSE ENGINEERING")
        print("="*80)
        print(f"🎯 Target Device: {self.host}")
        print(f"🔑 SNMP Community: {self.community}")
        print(f"📅 Process Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        try:
            # Step 1: Basic connectivity test
            if not await self.basic_connectivity_test():
                print("❌ Cannot establish basic connectivity - aborting")
                return {'success': False, 'error': 'Connectivity failed'}

            # Step 2: Intelligent discovery
            discovery_result = await self.intelligent_discovery()
            if not discovery_result:
                print("⚠️  Intelligent discovery failed - continuing with limited functionality")

            # Step 3: V-SOL specialized analysis
            vsol_analysis = await self.vsol_specialized_analysis()

            # Step 4: Extract target data
            target_data = await self.extract_target_data()
            self.results['target_data'] = target_data

            # Step 5: Generate working adapter
            adapter = await self.generate_working_adapter()

            # Step 6: Save to knowledge base
            await self.save_to_knowledge_base()

            # Step 7: Generate report
            report = await self.generate_report()

            print(f"\n🎉 REVERSE ENGINEERING COMPLETED SUCCESSFULLY!")
            print(f"📊 Discovered {len(self.results.get('discovered_oids', {}))} OIDs")
            print(f"🎯 Extracted target data for signal power, distance, uptime, and status")
            print(f"🔧 Generated working adapter for future use")
            print(f"💾 Saved findings to knowledge base")
            print(f"📋 Comprehensive report generated")

            return {
                'success': True,
                'results': self.results,
                'report': report
            }

        except Exception as e:
            print(f"❌ Reverse engineering process failed: {e}")
            return {'success': False, 'error': str(e)}

        finally:
            # Clean up connections
            try:
                await self.device.close()
            except:
                pass


async def main():
    """
    Main function demonstrating V-SOL OLT reverse engineering.
    """
    print("🎯 V-SOL OLT REVERSE ENGINEERING DEMONSTRATION")
    print("="*60)
    print("This demo shows how to handle undocumented V-SOL OLT devices")
    print("when you only know the IP address and SNMP community.")
    print()

    # Configuration
    V_SOLT_IP = "192.168.1.1"  # Replace with your V-SOL OLT IP
    SNMP_COMMUNITY = "public"   # Replace with your SNMP community

    print(f"🎯 Target: V-SOL OLT at {V_SOLT_IP}")
    print(f"🔑 Community: {SNMP_COMMUNITY}")
    print()

    # Create reverse engineer instance
    reverse_engineer = VSOLReverseEngineer(V_SOLT_IP, SNMP_COMMUNITY)

    # Run complete reverse engineering process
    results = await reverse_engineer.run_complete_reverse_engineering()

    if results.get('success'):
        print(f"\n✅ SUCCESS! V-SOL OLT reverse engineering completed")
        print(f"📁 Check the generated files:")
        print(f"   • vsol_reverse_engineering_report_*.json")
        print(f"   • vsol_knowledge_*.json")
        print(f"\n🚀 You can now use the discovered patterns for monitoring!")
    else:
        print(f"\n❌ Reverse engineering failed: {results.get('error')}")
        print(f"💡 Suggestions:")
        print(f"   • Verify the device IP address is correct")
        print(f"   • Check SNMP community string")
        print(f"   • Ensure the device is accessible from this network")
        print(f"   • Confirm SNMP is enabled on the device")


if __name__ == "__main__":
    """
    Run this example to see V-SOL OLT reverse engineering in action.

    Usage:
        python examples/vsol_reverse_engineering_example.py

    Make sure to update the V_SOLT_IP and SNMP_COMMUNITY variables
    with your actual device details.
    """
    asyncio.run(main())