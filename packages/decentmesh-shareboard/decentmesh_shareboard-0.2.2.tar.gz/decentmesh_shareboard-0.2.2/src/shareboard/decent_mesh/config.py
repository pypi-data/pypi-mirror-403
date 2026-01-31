"""
Configuration loader for DecentMesh Python SDK.

Loads network configuration from TOML files, providing seed relays
and network parameters.

Usage:
    from shareboard.decent_mesh.config import load_config, NetworkConfig
    
    # Load from default location
    config = load_config()
    
    # Load from custom path
    config = load_config("/path/to/config.toml")
    
    # Access values
    for relay in config.relays:
        print(f"{relay.name}: {relay.address}")
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback for older Python


@dataclass
class RelayConfig:
    """
    Configuration for a single relay node.
    
    Attributes:
        address: Relay address (host:port)
        name: Friendly display name
        region: Geographic/logical region
    """
    address: str
    name: str = ""
    region: str = ""


@dataclass
class NetworkConfig:
    """
    Network configuration loaded from TOML.
    
    Attributes:
        relays: List of seed relay configurations
        target_relay_count: Desired number of connections
        refresh_interval_secs: Maintenance interval
        min_hops: Minimum circuit hops
        max_hops: Maximum circuit hops
    """
    relays: List[RelayConfig] = field(default_factory=list)
    target_relay_count: int = 5
    refresh_interval_secs: int = 10
    min_hops: int = 1
    max_hops: int = 3
    
    @property
    def seed_addresses(self) -> List[str]:
        """Get list of relay addresses only."""
        return [r.address for r in self.relays]
    
    @property
    def production_relays(self) -> List[RelayConfig]:
        """Get only production relays."""
        return [r for r in self.relays if r.region == "production"]


# Default config paths to search (in order)
DEFAULT_CONFIG_PATHS = [
    "config.toml",
    "decent_mesh.toml",
    os.path.join(os.path.dirname(__file__), "config.toml"),
]


def load_config(path: Optional[str] = None) -> NetworkConfig:
    """
    Load configuration from TOML file.
    
    Args:
        path: Path to config file. If None, searches default locations.
        
    Returns:
        NetworkConfig with loaded values (uses defaults if file not found)
        
    Raises:
        FileNotFoundError: If path specified but doesn't exist
    """
    config_path = None
    
    if path:
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
    else:
        # Search default locations
        for default_path in DEFAULT_CONFIG_PATHS:
            p = Path(default_path)
            if p.exists():
                config_path = p
                break
    
    if config_path is None:
        # Return default config with hardcoded production relays
        return _default_config()
    
    return _parse_config(config_path)


def _parse_config(path: Path) -> NetworkConfig:
    """Parse TOML config file."""
    with open(path, "rb") as f:
        data = tomllib.load(f)
    
    network = data.get("network", {})
    
    # Parse relays
    relays = []
    for relay_data in network.get("relays", []):
        relays.append(RelayConfig(
            address=relay_data.get("address", ""),
            name=relay_data.get("name", ""),
            region=relay_data.get("region", ""),
        ))
    
    return NetworkConfig(
        relays=relays,
        target_relay_count=network.get("target_relay_count", 5),
        refresh_interval_secs=network.get("refresh_interval_secs", 10),
        min_hops=network.get("min_hops", 1),
        max_hops=network.get("max_hops", 3),
    )


def _default_config() -> NetworkConfig:
    """Return default config with production relays."""
    return NetworkConfig(
        relays=[
            RelayConfig("fe.decentmesh.net:8888", "DecentMesh FE", "production"),
            RelayConfig("fa.decentmesh.net:8888", "DecentMesh FA", "production"),
            RelayConfig("93.153.22.172:8888", "DecentMesh IP Relay", "production"),
            RelayConfig("cn.decentmesh.net:8888", "DecentMesh CN", "production"),
        ],
        target_relay_count=5,
        refresh_interval_secs=10,
    )


def get_config_path() -> Optional[Path]:
    """Find config file path without loading."""
    for default_path in DEFAULT_CONFIG_PATHS:
        p = Path(default_path)
        if p.exists():
            return p
    return None
