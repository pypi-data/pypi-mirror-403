"""
Configuration manager for adapter configs and device profiles.
"""

import yaml
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from .adapter import AdapterConfig

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages adapter configurations and device profiles.

    Features:
    - Load adapter configs from YAML files
    - Manage device profile database
    - Provide configuration validation
    - Support for config inheritance
    - Hot-reload of configurations
    """

    def __init__(self, config_dir: str = "configs"):
        """
        Initialize configuration manager.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.adapters: Dict[str, AdapterConfig] = {}
        self.device_profiles: Dict[str, Dict[str, Any]] = {}
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(exist_ok=True)
        (self.config_dir / "adapters").mkdir(exist_ok=True)
        (self.config_dir / "profiles").mkdir(exist_ok=True)

    def load_adapter_configs(self):
        """Load all adapter configurations."""
        adapters_dir = self.config_dir / "adapters"
        if not adapters_dir.exists():
            logger.warning(f"Adapters directory not found: {adapters_dir}")
            return

        for yaml_file in adapters_dir.glob("*.yaml"):
            try:
                adapter_config = AdapterConfig.from_yaml(str(yaml_file))
                key = f"{adapter_config.vendor}_{adapter_config.device_type}"
                self.adapters[key] = adapter_config
                logger.info(f"Loaded adapter config: {key}")
            except Exception as e:
                logger.error(f"Failed to load adapter config {yaml_file}: {e}")

    def get_adapter_config(self, vendor: str, device_type: str) -> Optional[AdapterConfig]:
        """
        Get adapter configuration for vendor and device type.

        Args:
            vendor: Device vendor
            device_type: Device type

        Returns:
            AdapterConfig or None if not found
        """
        key = f"{vendor}_{device_type}"
        return self.adapters.get(key)

    def list_adapters(self) -> List[str]:
        """List all available adapter configurations."""
        return list(self.adapters.keys())

    def save_adapter_config(self, adapter_config: AdapterConfig):
        """Save adapter configuration to file."""
        adapters_dir = self.config_dir / "adapters"
        filename = f"{adapter_config.vendor}_{adapter_config.device_type}.yaml"
        filepath = adapters_dir / filename

        with open(filepath, 'w') as f:
            yaml.dump(adapter_config.to_dict(), f, default_flow_style=False, indent=2)

        # Update in-memory config
        key = f"{adapter_config.vendor}_{adapter_config.device_type}"
        self.adapters[key] = adapter_config

        logger.info(f"Saved adapter config: {filename}")

    def create_sample_configs(self):
        """Create sample adapter configurations."""
        # Huawei OLT adapter
        huawei_olt_config = {
            "name": "huawei-olt-ma5800",
            "version": "1.0.0",
            "device_type": "olt",
            "vendor": "huawei",
            "supported_models": ["MA5800-X7", "MA5800-X15", "MA5600T"],
            "default_community": "public",
            "default_version": "v2c",
            "default_timeout": 5,
            "default_retries": 3,
            "oid_mappings": [
                {
                    "name": "system_description",
                    "oid": "1.3.6.1.2.1.1.1.0",
                    "description": "System description",
                    "data_type": "string",
                    "category": "system"
                },
                {
                    "name": "system_uptime",
                    "oid": "1.3.6.1.2.1.1.3.0",
                    "description": "System uptime in timeticks",
                    "data_type": "integer",
                    "category": "system"
                },
                {
                    "name": "cpu_usage",
                    "oid": "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.5",
                    "description": "CPU usage percentage",
                    "data_type": "integer",
                    "unit": "percent",
                    "category": "performance"
                },
                {
                    "name": "memory_total",
                    "oid": "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.7",
                    "description": "Total memory in KB",
                    "data_type": "integer",
                    "unit": "KB",
                    "category": "performance"
                },
                {
                    "name": "memory_used",
                    "oid": "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.8",
                    "description": "Used memory in KB",
                    "data_type": "integer",
                    "unit": "KB",
                    "category": "performance"
                },
                {
                    "name": "huawei_gpon_board_info",
                    "oid": "1.3.6.1.4.1.2011.6.128.1.1.1",
                    "description": "GPON board information",
                    "data_type": "walk",
                    "category": "gpon"
                },
                {
                    "name": "huawei_ont_info",
                    "oid": "1.3.6.1.4.1.2011.6.128.1.1.3",
                    "description": "ONT information",
                    "data_type": "walk",
                    "category": "gpon"
                },
                {
                    "name": "huawei_optical_info",
                    "oid": "1.3.6.1.4.1.2011.6.128.1.1.4",
                    "description": "Optical monitoring information",
                    "data_type": "walk",
                    "category": "optical"
                }
            ],
            "transforms": [
                {
                    "name": "uptime_ticks_to_days",
                    "input_pattern": "system_uptime",
                    "output_field": "uptime_days",
                    "transformation_type": "scale",
                    "parameters": {"scale_factor": 0.000864, "unit": "days"}
                },
                {
                    "name": "memory_kb_to_mb",
                    "input_pattern": "memory_.*",
                    "output_field": "{field}_mb",
                    "transformation_type": "scale",
                    "parameters": {"scale_factor": 0.001024, "unit": "MB"}
                },
                {
                    "name": "calculate_memory_usage_percent",
                    "input_pattern": "memory_used",
                    "output_field": "memory_usage_percent",
                    "transformation_type": "calculate",
                    "parameters": {
                        "formula": "(memory_used / memory_total) * 100",
                        "unit": "percent"
                    }
                }
            ],
            "discovery_patterns": {
                "description_patterns": [
                    r"Huawei.*OLT",
                    r"MA5800",
                    r"MA5600T",
                    r"VRP.*software"
                ],
                "oid_prefixes": [
                    "1.3.6.1.4.1.2011",
                    "1.3.6.1.4.1.2011.6.128"
                ]
            },
            "collection_strategy": {
                "use_bulk_walk": True,
                "max_repetitions": 20,
                "concurrent_requests": 10,
                "cache_ttl_minutes": 5
            }
        }

        # Save Huawei OLT config
        self._save_sample_config("huawei_olt", huawei_olt_config)

        # ZTE OLT adapter
        zte_olt_config = {
            "name": "zte-olt-zxa10",
            "version": "1.0.0",
            "device_type": "olt",
            "vendor": "zte",
            "supported_models": ["ZXA10 C200", "ZXA10 C220", "ZXA10 C300"],
            "default_community": "public",
            "default_version": "v2c",
            "default_timeout": 5,
            "default_retries": 3,
            "oid_mappings": [
                {
                    "name": "zte_slot_info",
                    "oid": "1.3.6.1.4.1.3902.110.1.1",
                    "description": "ZTE slot information",
                    "data_type": "walk",
                    "category": "system"
                },
                {
                    "name": "zte_pon_port_info",
                    "oid": "1.3.6.1.4.1.3902.110.1.2",
                    "description": "PON port information",
                    "data_type": "walk",
                    "category": "gpon"
                },
                {
                    "name": "zte_onu_info",
                    "oid": "1.3.6.1.4.1.3902.110.1.3",
                    "description": "ONU information",
                    "data_type": "walk",
                    "category": "gpon"
                }
            ],
            "discovery_patterns": {
                "description_patterns": [
                    r"ZTE.*OLT",
                    r"ZXA10",
                    r"ZXAN"
                ],
                "oid_prefixes": [
                    "1.3.6.1.4.1.3902",
                    "1.3.6.1.4.1.3902.110"
                ]
            }
        }

        self._save_sample_config("zte_olt", zte_olt_config)

        # V-SOL OLT adapter
        vsol_olt_config = {
            "name": "vsol-olt-v1600",
            "version": "1.0.0",
            "device_type": "olt",
            "vendor": "vsol",
            "supported_models": ["V1600D", "V1600G", "V2801RH"],
            "default_community": "public",
            "default_version": "v2c",
            "default_timeout": 5,
            "default_retries": 3,
            "oid_mappings": [
                {
                    "name": "vsol_system_info",
                    "oid": "1.3.6.1.4.1.39926.1",
                    "description": "V-SOL system information",
                    "data_type": "walk",
                    "category": "system"
                },
                {
                    "name": "vsol_interface_info",
                    "oid": "1.3.6.1.4.1.39926.2",
                    "description": "Interface information",
                    "data_type": "walk",
                    "category": "interfaces"
                },
                {
                    "name": "vsol_gpon_info",
                    "oid": "1.3.6.1.4.1.39926.3",
                    "description": "GPON information",
                    "data_type": "walk",
                    "category": "gpon"
                }
            ],
            "discovery_patterns": {
                "description_patterns": [
                    r"V-SOL",
                    r"V1600",
                    r"V2801"
                ],
                "oid_prefixes": [
                    "1.3.6.1.4.1.39926"
                ]
            }
        }

        self._save_sample_config("vsol_olt", vsol_olt_config)

        logger.info("Created sample adapter configurations")

    def _save_sample_config(self, name: str, config_data: Dict[str, Any]):
        """Save sample configuration to file."""
        adapters_dir = self.config_dir / "adapters"
        filename = f"{name}.yaml"
        filepath = adapters_dir / filename

        with open(filepath, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)

        logger.info(f"Created sample config: {filename}")

    def validate_config(self, config: AdapterConfig) -> List[str]:
        """
        Validate adapter configuration.

        Args:
            config: Adapter configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Check required fields
        if not config.name:
            errors.append("Adapter name is required")

        if not config.device_type:
            errors.append("Device type is required")

        if not config.vendor:
            errors.append("Vendor is required")

        # Validate OID mappings
        for oid_mapping in config.oid_mappings:
            if not oid_mapping.name:
                errors.append(f"OID mapping name is required for {config.name}")
            if not oid_mapping.oid:
                errors.append(f"OID is required for mapping {oid_mapping.name}")

            # Validate OID format
            if not oid_mapping.oid.replace(".", "").replace(" ", "").isdigit():
                errors.append(f"Invalid OID format: {oid_mapping.oid}")

        return errors

    def get_supported_vendors(self) -> List[str]:
        """Get list of supported vendors."""
        vendors = set()
        for adapter in self.adapters.values():
            vendors.add(adapter.vendor)
        return sorted(list(vendors))

    def get_supported_device_types(self) -> List[str]:
        """Get list of supported device types."""
        types = set()
        for adapter in self.adapters.values():
            types.add(adapter.device_type)
        return sorted(list(types))