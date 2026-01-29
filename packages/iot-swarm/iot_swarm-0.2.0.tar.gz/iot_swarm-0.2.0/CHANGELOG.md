# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-01-23

### Added

- **Energy Metrics** (`swarm_orchestrator.metrics.energy`)
  - `EnergyCollector` for hardware-based power monitoring
  - Device power profiles for RPi 4, RPi Zero, ESP32, etc.
  - CPU temperature reading from Linux sysfs
  - Battery level monitoring for portable devices
  - Carbon footprint tracking with configurable grid intensity
  - Energy efficiency scoring (A+ to F rating)
  - Power states: active, idle, low_power, critical

- **Adaptive Gossip** (`swarm_orchestrator.gossip.adaptive`)
  - `AdaptiveGossip` controller for dynamic parameter adjustment
  - Four gossip modes: aggressive, normal, conservative, emergency
  - Network health monitoring with loss rate detection
  - Activity-based interval adjustment
  - Swarm size-aware fanout scaling
  - Energy-aware mode switching (reduces gossip on low battery)

- **Green Dashboard** (`swarm_orchestrator.metrics.green_dashboard`)
  - Energy-focused terminal dashboard with Rich
  - Real-time power consumption with sparkline graphs
  - Efficiency rating display (A+ to F)
  - Carbon footprint visualization
  - Adaptive gossip mode indicator
  - Per-node power and efficiency in swarm table

- **New CLI Commands**
  - `swarm swarm green` - Launch green energy dashboard
  - `swarm swarm energy [--json]` - Show energy metrics

- **New Configuration Sections**
  - `[energy]` - Energy collection settings
    - `carbon_intensity_gco2_kwh` - Grid carbon intensity
    - `power_budget_watts` - Optional power budget
    - `low_power_threshold_percent` - Battery threshold
  - `[adaptive_gossip]` - Adaptive gossip settings
    - `min_interval_ms` / `max_interval_ms` - Interval bounds
    - `max_fanout` - Maximum fanout limit
    - `energy_aware` - Enable energy-based adaptation

### Changed

- Node now initializes energy collector and adaptive gossip on start
- `node.get_status()` includes energy and adaptive gossip info
- Configuration template updated with new sections

## [0.1.0] - 2025-01-23

### Added

- Initial release
- Core models: `NodeState`, `Message`, `SwarmState`, `DeviceClass`, `NodeRole`, `NodeStatus`
- Gossip protocol with UDP multicast discovery and unicast state propagation
- Leader election with Raft-inspired term-based voting
- Device class support: full, standard, and minimal
- Metrics collection: CPU, memory, message counts, energy estimation
- Rich terminal dashboard for swarm monitoring
- TOML configuration system
- CLI commands:
  - `swarm node start/stop/status` - Node management
  - `swarm swarm status/dashboard/metrics` - Swarm operations
  - `swarm config init/show/set/path` - Configuration management

### Technical Details

- Python 3.11+ required
- Dependencies: typer, pydantic v2, pydantic-settings, rich, toml
- Optional: psutil for metrics collection
- UDP multicast on 239.255.255.250:5556 for discovery
- UDP unicast on port 5555 for gossip
- Gossip interval: 1 second
- Anti-entropy sync: 10 seconds
- Election timeout: 1.5-3 seconds
- Heartbeat interval: 500ms

## [Unreleased]

### Planned for v0.2.0

- Advanced energy metrics from hardware sensors
- Adaptive gossip intervals based on network conditions
- Green dashboard with energy visualizations
- Power-aware leader election

### Planned for v0.3.0

- MicroPython compatibility layer
- Reduced memory footprint for constrained devices

### Planned for v0.4.0

- UART/I2C whisper protocol for non-WiFi devices
- Gateway node support for bridging networks

### Planned for v0.5.0

- TinyML energy prediction models
- Predictive task scheduling
