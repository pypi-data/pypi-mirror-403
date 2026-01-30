# SNMP Manager - Telecom Multivendor Data Collection System

[![PyPI version](https://badge.fury.io/py/snmp-manager.svg)](https://badge.fury.io/py/snmp-manager)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A robust, intelligent SNMP data collection system capable of handling multivendor telecom devices (OLT/ONU, BSC/RNC, etc.) with automatic discovery, reverse engineering capabilities, and uniform data output.

## Features

- **Intelligent Device Discovery** - Automatically discover and profile SNMP devices
- **Adaptive Adapter System** - Self-learning adapters that evolve with each device
- **Reverse Engineering** - Handle undocumented devices through pattern recognition
- **Uniform Data Output** - Standardized JSON/XML/YAML output for all devices
- **High Performance** - Parallel collection and intelligent caching
- **Crowdsourced Knowledge** - Community-driven device profile database
- **Pattern Recognition** - ML-like device classification with confidence scoring
- **Self-Learning** - Gets smarter with every device interaction
- **Robust Fallback Strategies** - Multiple collection methods with graceful degradation

## Quick Start

```python
from snmp_manager import SNMPManager

# Discover devices on network
async with SNMPManager() as manager:
    devices = await manager.discover_devices("192.168.1.0/24")

    # Collect data from all devices
    for device in devices:
        data = await device.collect()
        print(f"Device {device.host}: {len(data)} fields collected")
```

## Use Case Example

```python
# Enhanced device with full intelligence features
from snmp_manager.core.enhanced_device import EnhancedDevice

async def main():
    # Create enhanced device (no manual configuration needed!)
    device = EnhancedDevice(host="192.168.1.10")

    # Intelligent discovery (reverse engineers unknown devices!)
    discovery = await device.intelligent_discover()
    print(f"Discovered {discovery['total_duration_ms']:.1f}ms")

    # Smart data collection with fallback strategies
    data = await device.collect_with_intelligence()
    print(f"Collected {len(data)} fields")

    # Get device insights
    insights = await device.get_intelligent_insights()
    print(f"Device classification: {insights['device_info']['signature']}")

asyncio.run(main())
```

## Supported Devices

### Telecom Equipment
- **OLT/ONU**: Huawei (MA5800, MA5600), ZTE (ZXA10), V-SOL (V1600, V2800), Fiberhome (AN5500)
- **Cellular**: BSC, RNC, SMSC, BTS, mobile network equipment
- **GPON/EPON**: All major OLT and ONU/ONT devices
- **Network Switches**: Cisco, Juniper, Huawei, ZTE, Mikrotik
- **Routers**: Enterprise and carrier-grade routers

### Vendor Support
- **Documented**: Huawei, ZTE, Cisco, Juniper, Mikrotik
- **Undocumented**: V-SOL, C-Data, Fiberhome (via reverse engineering)
- **Unknown**: Any SNMP device (pattern recognition + learning)

## Installation

```bash
# From PyPI
pip install snmp-manager

# With optional ML features
pip install snmp-manager[ml]

# With development tools
pip install snmp-manager[dev]

# From source
git clone https://github.com/mexyusef/snmp-manager.git
cd snmp-manager
pip install -e .
```

## Documentation

- [**Examples**](examples/) - Usage examples and demos

## Development

```bash
# Clone repository
git clone https://github.com/mexyusef/snmp-manager.git
cd snmp-manager

# Install development dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/

# Build documentation
mkdocs build
```

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

Copyright © 2025 Yusef Ulum

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **GitHub Repository**: https://github.com/mexyusef/snmp-manager
- **PyPI Package**: https://pypi.org/project/snmp-manager/
- **Documentation**: https://snmp-manager.readthedocs.io/
- **Bug Reports**: https://github.com/mexyusef/snmp-manager/issues
- **Discussions**: https://github.com/mexyusef/snmp-manager/discussions
