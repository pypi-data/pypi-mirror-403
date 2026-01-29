"""Energy metrics collection and analysis for v0.2.0."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swarm_orchestrator.config import SwarmConfig
    from swarm_orchestrator.models import DeviceClass, NodeState


class PowerState(str, Enum):
    """Power state of the device."""

    ACTIVE = "active"  # Normal operation
    IDLE = "idle"  # Low activity
    LOW_POWER = "low_power"  # Energy saving mode
    CRITICAL = "critical"  # Battery critical


@dataclass
class DevicePowerProfile:
    """Power profile for a device class."""

    device_class: str
    tdp_watts: float  # Thermal Design Power
    idle_watts: float  # Power at idle
    min_watts: float  # Minimum power draw
    max_watts: float  # Maximum power draw
    has_battery: bool = False
    battery_capacity_wh: float = 0.0  # Watt-hours


# Default power profiles for common devices
POWER_PROFILES = {
    "full": DevicePowerProfile(
        device_class="full",
        tdp_watts=7.5,  # RPi 4
        idle_watts=2.7,
        min_watts=2.0,
        max_watts=7.5,
    ),
    "standard": DevicePowerProfile(
        device_class="standard",
        tdp_watts=1.5,  # RPi Zero 2W / ESP32-S3
        idle_watts=0.4,
        min_watts=0.1,
        max_watts=1.5,
    ),
    "minimal": DevicePowerProfile(
        device_class="minimal",
        tdp_watts=0.5,  # ESP32
        idle_watts=0.02,
        min_watts=0.01,
        max_watts=0.5,
        has_battery=True,
        battery_capacity_wh=3.7,  # Typical LiPo
    ),
}


@dataclass
class EnergySample:
    """A single energy measurement sample."""

    timestamp: datetime
    power_watts: float  # Current power draw
    energy_joules: float  # Energy consumed since last sample
    cpu_temp_celsius: float | None  # CPU temperature
    voltage_v: float | None  # Supply voltage
    battery_percent: float | None  # Battery level (if applicable)
    power_state: PowerState
    carbon_intensity_gco2_kwh: float  # Grid carbon intensity


@dataclass
class EnergyStats:
    """Aggregated energy statistics."""

    total_energy_joules: float = 0.0
    total_energy_wh: float = 0.0
    avg_power_watts: float = 0.0
    peak_power_watts: float = 0.0
    min_power_watts: float = float("inf")
    total_carbon_grams: float = 0.0
    efficiency_score: float = 100.0  # 0-100, higher is better
    samples_count: int = 0
    uptime_seconds: float = 0.0

    def update(self, sample: EnergySample, interval_seconds: float) -> None:
        """Update stats with a new sample."""
        self.total_energy_joules += sample.energy_joules
        self.total_energy_wh = self.total_energy_joules / 3600.0
        self.peak_power_watts = max(self.peak_power_watts, sample.power_watts)
        self.min_power_watts = min(self.min_power_watts, sample.power_watts)
        self.samples_count += 1
        self.uptime_seconds += interval_seconds

        # Running average
        if self.samples_count > 0:
            self.avg_power_watts = (
                (self.avg_power_watts * (self.samples_count - 1) + sample.power_watts)
                / self.samples_count
            )

        # Carbon footprint: gCO2 = kWh * gCO2/kWh
        energy_kwh = sample.energy_joules / 3_600_000.0
        self.total_carbon_grams += energy_kwh * sample.carbon_intensity_gco2_kwh


class EnergyCollector:
    """Collect energy metrics from hardware sensors."""

    def __init__(
        self,
        node_state: "NodeState",
        config: "SwarmConfig",
        power_profile: DevicePowerProfile | None = None,
    ):
        self.node_state = node_state
        self.config = config

        # Get power profile for device class
        device_class = node_state.device_class.value
        self.power_profile = power_profile or POWER_PROFILES.get(
            device_class, POWER_PROFILES["standard"]
        )

        self.stats = EnergyStats()
        self._samples: list[EnergySample] = []
        self._max_samples = config.metrics.history_size

        self._running = False
        self._collect_task: asyncio.Task | None = None
        self._last_collect_time = datetime.now()

        # Hardware sensor paths (Linux sysfs)
        self._cpu_temp_path = Path("/sys/class/thermal/thermal_zone0/temp")
        self._voltage_path = Path("/sys/class/hwmon/hwmon0/in0_input")
        self._battery_path = Path("/sys/class/power_supply/BAT0/capacity")

        # Default carbon intensity (gCO2/kWh) - can be updated dynamically
        self._carbon_intensity = config.energy.carbon_intensity_gco2_kwh

    async def start(self) -> None:
        """Start energy collection."""
        if self._running:
            return

        self._running = True
        self._last_collect_time = datetime.now()

        loop = asyncio.get_event_loop()
        self._collect_task = loop.create_task(self._collection_loop())

    async def stop(self) -> None:
        """Stop energy collection."""
        self._running = False

        if self._collect_task:
            self._collect_task.cancel()
            try:
                await self._collect_task
            except asyncio.CancelledError:
                pass

    async def _collection_loop(self) -> None:
        """Periodically collect energy metrics."""
        interval = self.config.energy.collection_interval_ms / 1000.0

        while self._running:
            try:
                await asyncio.sleep(interval)
                sample = self._collect_sample(interval)
                self._samples.append(sample)
                self.stats.update(sample, interval)

                # Prune old samples
                while len(self._samples) > self._max_samples:
                    self._samples.pop(0)

                # Update efficiency score
                self._update_efficiency_score()

            except asyncio.CancelledError:
                break
            except Exception:
                pass

    def _collect_sample(self, interval_seconds: float) -> EnergySample:
        """Collect a single energy sample."""
        # Read hardware sensors
        cpu_temp = self._read_cpu_temp()
        voltage = self._read_voltage()
        battery = self._read_battery()

        # Estimate power from CPU usage
        cpu_percent = self.node_state.metrics.get("cpu_percent", 0.0)
        power_watts = self._estimate_power(cpu_percent)

        # Calculate energy for this interval
        energy_joules = power_watts * interval_seconds

        # Determine power state
        power_state = self._determine_power_state(cpu_percent, battery)

        return EnergySample(
            timestamp=datetime.now(),
            power_watts=power_watts,
            energy_joules=energy_joules,
            cpu_temp_celsius=cpu_temp,
            voltage_v=voltage,
            battery_percent=battery,
            power_state=power_state,
            carbon_intensity_gco2_kwh=self._carbon_intensity,
        )

    def _estimate_power(self, cpu_percent: float) -> float:
        """Estimate power consumption based on CPU usage."""
        # Linear interpolation between idle and TDP
        profile = self.power_profile
        power_range = profile.tdp_watts - profile.idle_watts
        estimated = profile.idle_watts + (power_range * cpu_percent / 100.0)
        return max(profile.min_watts, min(profile.max_watts, estimated))

    def _read_cpu_temp(self) -> float | None:
        """Read CPU temperature from sysfs."""
        try:
            if self._cpu_temp_path.exists():
                temp_milli = int(self._cpu_temp_path.read_text().strip())
                return temp_milli / 1000.0
        except Exception:
            pass
        return None

    def _read_voltage(self) -> float | None:
        """Read supply voltage from sysfs."""
        try:
            if self._voltage_path.exists():
                voltage_milli = int(self._voltage_path.read_text().strip())
                return voltage_milli / 1000.0
        except Exception:
            pass
        return None

    def _read_battery(self) -> float | None:
        """Read battery level from sysfs."""
        try:
            if self._battery_path.exists():
                return float(self._battery_path.read_text().strip())
        except Exception:
            pass
        return None

    def _determine_power_state(
        self, cpu_percent: float, battery: float | None
    ) -> PowerState:
        """Determine current power state."""
        if battery is not None:
            if battery < 10:
                return PowerState.CRITICAL
            if battery < 30:
                return PowerState.LOW_POWER

        if cpu_percent < 5:
            return PowerState.IDLE

        return PowerState.ACTIVE

    def _update_efficiency_score(self) -> None:
        """Calculate energy efficiency score (0-100)."""
        if not self._samples:
            return

        # Factors for efficiency scoring:
        # 1. Power usage relative to TDP (lower is better)
        # 2. Work done per watt (messages per joule)
        # 3. Temperature (lower is better)

        profile = self.power_profile
        power_ratio = self.stats.avg_power_watts / profile.tdp_watts

        # Base score from power efficiency
        power_score = max(0, 100 - (power_ratio * 50))

        # Bonus for work efficiency
        messages = self.node_state.metrics.get("messages_sent", 0) + \
                   self.node_state.metrics.get("messages_received", 0)
        if self.stats.total_energy_joules > 0:
            messages_per_joule = messages / self.stats.total_energy_joules
            work_bonus = min(20, messages_per_joule * 10)
        else:
            work_bonus = 0

        # Temperature penalty
        temp_penalty = 0
        recent_temps = [s.cpu_temp_celsius for s in self._samples[-10:] if s.cpu_temp_celsius]
        if recent_temps:
            avg_temp = sum(recent_temps) / len(recent_temps)
            if avg_temp > 70:
                temp_penalty = min(20, (avg_temp - 70) * 2)

        self.stats.efficiency_score = max(0, min(100, power_score + work_bonus - temp_penalty))

    def set_carbon_intensity(self, gco2_per_kwh: float) -> None:
        """Update carbon intensity (e.g., from grid data API)."""
        self._carbon_intensity = gco2_per_kwh

    def get_latest_sample(self) -> EnergySample | None:
        """Get the most recent energy sample."""
        return self._samples[-1] if self._samples else None

    def get_recent_samples(self, count: int = 10) -> list[EnergySample]:
        """Get recent energy samples."""
        return self._samples[-count:]

    def get_summary(self) -> dict:
        """Get energy metrics summary."""
        latest = self.get_latest_sample()
        return {
            "power_watts": round(latest.power_watts, 2) if latest else 0.0,
            "power_state": latest.power_state.value if latest else "unknown",
            "cpu_temp_c": round(latest.cpu_temp_celsius, 1) if latest and latest.cpu_temp_celsius else None,
            "battery_percent": latest.battery_percent if latest else None,
            "total_energy_wh": round(self.stats.total_energy_wh, 4),
            "total_energy_j": round(self.stats.total_energy_joules, 2),
            "avg_power_watts": round(self.stats.avg_power_watts, 2),
            "peak_power_watts": round(self.stats.peak_power_watts, 2),
            "carbon_grams": round(self.stats.total_carbon_grams, 4),
            "efficiency_score": round(self.stats.efficiency_score, 1),
            "device_tdp_watts": self.power_profile.tdp_watts,
            "samples_count": self.stats.samples_count,
        }
