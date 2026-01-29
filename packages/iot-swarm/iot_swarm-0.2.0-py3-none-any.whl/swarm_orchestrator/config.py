"""TOML configuration management."""

from pathlib import Path
from typing import Any

import toml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_CONFIG_DIR = Path.home() / ".config" / "swarm_orchestrator"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.toml"


class NetworkSettings(BaseModel):
    """Network configuration."""

    gossip_port: int = 5555
    multicast_group: str = "239.255.255.250"
    multicast_port: int = 5556
    bind_address: str = "0.0.0.0"


class GossipSettings(BaseModel):
    """Gossip protocol configuration."""

    interval_ms: int = 1000  # Gossip interval in milliseconds
    fanout: int = 3  # Number of nodes to gossip to each round
    ttl: int = 3  # Message time-to-live (hops)
    anti_entropy_interval_ms: int = 10000  # Full sync interval
    message_cache_size: int = 1000  # Max messages to track for deduplication


class ConsensusSettings(BaseModel):
    """Leader election configuration."""

    heartbeat_interval_ms: int = 500  # Leader heartbeat interval
    election_timeout_min_ms: int = 1500  # Minimum election timeout
    election_timeout_max_ms: int = 3000  # Maximum election timeout
    vote_timeout_ms: int = 1000  # Time to wait for votes


class NodeSettings(BaseModel):
    """Node-specific configuration."""

    name: str = ""  # Auto-generated if empty
    device_class: str = "standard"  # full, standard, minimal
    data_dir: Path = Field(default_factory=lambda: DEFAULT_CONFIG_DIR / "data")


class MetricsSettings(BaseModel):
    """Metrics collection configuration."""

    enabled: bool = True
    collection_interval_ms: int = 5000
    history_size: int = 100  # Number of samples to keep


class EnergySettings(BaseModel):
    """Energy metrics configuration (v0.2.0)."""

    enabled: bool = True
    collection_interval_ms: int = 1000  # More frequent for energy
    carbon_intensity_gco2_kwh: float = 400.0  # Default grid carbon intensity
    power_budget_watts: float | None = None  # Optional power budget
    low_power_threshold_percent: float = 30.0  # Battery threshold for low power mode
    critical_threshold_percent: float = 10.0  # Battery threshold for critical mode


class AdaptiveGossipSettings(BaseModel):
    """Adaptive gossip configuration (v0.2.0)."""

    enabled: bool = True
    adaptation_interval_ms: int = 5000  # How often to adapt
    min_interval_ms: int = 200  # Minimum gossip interval
    max_interval_ms: int = 5000  # Maximum gossip interval
    max_fanout: int = 10  # Maximum fanout
    energy_aware: bool = True  # Adjust based on energy state


class SwarmConfig(BaseSettings):
    """Main configuration for swarm orchestrator."""

    model_config = SettingsConfigDict(
        env_prefix="SWARM_",
        env_nested_delimiter="__",
    )

    network: NetworkSettings = Field(default_factory=NetworkSettings)
    gossip: GossipSettings = Field(default_factory=GossipSettings)
    consensus: ConsensusSettings = Field(default_factory=ConsensusSettings)
    node: NodeSettings = Field(default_factory=NodeSettings)
    metrics: MetricsSettings = Field(default_factory=MetricsSettings)
    energy: EnergySettings = Field(default_factory=EnergySettings)
    adaptive_gossip: AdaptiveGossipSettings = Field(default_factory=AdaptiveGossipSettings)

    @classmethod
    def load(cls, config_path: Path | None = None) -> "SwarmConfig":
        """Load configuration from TOML file."""
        path = config_path or DEFAULT_CONFIG_FILE
        if path.exists():
            data = toml.load(path)
            return cls(**data)
        return cls()

    def save(self, config_path: Path | None = None) -> None:
        """Save configuration to TOML file."""
        path = config_path or DEFAULT_CONFIG_FILE
        path.parent.mkdir(parents=True, exist_ok=True)

        data = self.model_dump(mode="json")
        # Convert Path objects to strings for TOML
        if "node" in data and "data_dir" in data["node"]:
            data["node"]["data_dir"] = str(data["node"]["data_dir"])

        with open(path, "w") as f:
            toml.dump(data, f)

    def get_nested(self, key: str) -> Any:
        """Get a nested config value by dot-separated key."""
        parts = key.split(".")
        obj: Any = self
        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                raise KeyError(f"Config key not found: {key}")
        return obj

    def set_nested(self, key: str, value: Any) -> None:
        """Set a nested config value by dot-separated key."""
        parts = key.split(".")
        obj = self
        for part in parts[:-1]:
            obj = getattr(obj, part)

        final_key = parts[-1]
        if hasattr(obj, final_key):
            # Type coercion based on current type
            current = getattr(obj, final_key)
            if isinstance(current, bool):
                value = value.lower() in ("true", "1", "yes") if isinstance(value, str) else bool(value)
            elif isinstance(current, int):
                value = int(value)
            elif isinstance(current, float):
                value = float(value)
            elif isinstance(current, Path):
                value = Path(value)
            setattr(obj, final_key, value)
        else:
            raise KeyError(f"Config key not found: {key}")


def get_config_path() -> Path:
    """Get the default config file path."""
    return DEFAULT_CONFIG_FILE


def init_config(force: bool = False) -> Path:
    """Initialize a new config file with defaults."""
    path = DEFAULT_CONFIG_FILE
    if path.exists() and not force:
        raise FileExistsError(f"Config file already exists: {path}")

    config = SwarmConfig()
    config.save(path)
    return path


def load_config(config_path: Path | None = None) -> SwarmConfig:
    """Load configuration, creating defaults if needed."""
    return SwarmConfig.load(config_path)


DEFAULT_CONFIG_TEMPLATE = """\
# Swarm Orchestrator Configuration v0.2.0
# See documentation for all options

[network]
gossip_port = 5555
multicast_group = "239.255.255.250"
multicast_port = 5556
bind_address = "0.0.0.0"

[gossip]
interval_ms = 1000
fanout = 3
ttl = 3
anti_entropy_interval_ms = 10000
message_cache_size = 1000

[consensus]
heartbeat_interval_ms = 500
election_timeout_min_ms = 1500
election_timeout_max_ms = 3000
vote_timeout_ms = 1000

[node]
name = ""
device_class = "standard"

[metrics]
enabled = true
collection_interval_ms = 5000
history_size = 100

[energy]
enabled = true
collection_interval_ms = 1000
carbon_intensity_gco2_kwh = 400.0
low_power_threshold_percent = 30.0
critical_threshold_percent = 10.0

[adaptive_gossip]
enabled = true
adaptation_interval_ms = 5000
min_interval_ms = 200
max_interval_ms = 5000
max_fanout = 10
energy_aware = true
"""
