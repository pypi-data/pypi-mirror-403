"""
Adapter configuration system for device-specific collection rules.
"""

import yaml
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class OIDMapping:
    """OID mapping configuration."""
    name: str
    oid: str
    description: Optional[str] = None
    data_type: str = "string"  # string, integer, float, boolean
    unit: Optional[str] = None
    scale_factor: Optional[float] = None
    category: str = "general"


@dataclass
class TransformRule:
    """Data transformation rule."""
    name: str
    input_pattern: str
    output_field: str
    transformation_type: str  # scale, convert, format
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AdapterConfig:
    """Configuration for device adapter."""
    name: str
    version: str
    device_type: str
    vendor: str
    supported_models: List[str] = field(default_factory=list)

    # Connection settings
    default_community: str = "public"
    default_version: str = "v2c"
    default_timeout: int = 5
    default_retries: int = 3

    # OID mappings
    oid_mappings: List[OIDMapping] = field(default_factory=list)

    # Transformation rules
    transforms: List[TransformRule] = field(default_factory=list)

    # Discovery patterns
    discovery_patterns: Dict[str, List[str]] = field(default_factory=dict)

    # Collection strategy
    collection_strategy: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "AdapterConfig":
        """Load adapter config from YAML file."""
        try:
            with open(yaml_path, 'r') as f:
                config_data = yaml.safe_load(f)

            # Convert OID mappings
            oid_mappings = []
            for mapping_data in config_data.get("oid_mappings", []):
                oid_mappings.append(OIDMapping(**mapping_data))

            # Convert transforms
            transforms = []
            for transform_data in config_data.get("transforms", []):
                transforms.append(TransformRule(**transform_data))

            return cls(
                name=config_data["name"],
                version=config_data["version"],
                device_type=config_data["device_type"],
                vendor=config_data["vendor"],
                supported_models=config_data.get("supported_models", []),
                default_community=config_data.get("default_community", "public"),
                default_version=config_data.get("default_version", "v2c"),
                default_timeout=config_data.get("default_timeout", 5),
                default_retries=config_data.get("default_retries", 3),
                oid_mappings=oid_mappings,
                transforms=transforms,
                discovery_patterns=config_data.get("discovery_patterns", {}),
                collection_strategy=config_data.get("collection_strategy", {})
            )

        except Exception as e:
            logger.error(f"Failed to load adapter config from {yaml_path}: {e}")
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "device_type": self.device_type,
            "vendor": self.vendor,
            "supported_models": self.supported_models,
            "default_community": self.default_community,
            "default_version": self.default_version,
            "default_timeout": self.default_timeout,
            "default_retries": self.default_retries,
            "oid_mappings": [
                {
                    "name": m.name,
                    "oid": m.oid,
                    "description": m.description,
                    "data_type": m.data_type,
                    "unit": m.unit,
                    "scale_factor": m.scale_factor,
                    "category": m.category
                }
                for m in self.oid_mappings
            ],
            "transforms": [
                {
                    "name": t.name,
                    "input_pattern": t.input_pattern,
                    "output_field": t.output_field,
                    "transformation_type": t.transformation_type,
                    "parameters": t.parameters
                }
                for t in self.transforms
            ],
            "discovery_patterns": self.discovery_patterns,
            "collection_strategy": self.collection_strategy
        }