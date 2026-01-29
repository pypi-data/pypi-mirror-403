"""Metrics collection."""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swarm_orchestrator.config import SwarmConfig
    from swarm_orchestrator.models import NodeState


@dataclass
class MetricSample:
    """A single metric sample."""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    messages_sent: int
    messages_received: int
    gossip_rounds: int
    energy_estimate_mj: float  # Millijoules estimate


@dataclass
class MetricsState:
    """Aggregated metrics state."""

    samples: deque = field(default_factory=lambda: deque(maxlen=100))
    total_messages_sent: int = 0
    total_messages_received: int = 0
    total_gossip_rounds: int = 0
    start_time: datetime = field(default_factory=datetime.now)

    @property
    def latest(self) -> MetricSample | None:
        """Get most recent sample."""
        return self.samples[-1] if self.samples else None

    @property
    def avg_cpu(self) -> float:
        """Average CPU usage over samples."""
        if not self.samples:
            return 0.0
        return sum(s.cpu_percent for s in self.samples) / len(self.samples)

    @property
    def avg_memory(self) -> float:
        """Average memory usage over samples."""
        if not self.samples:
            return 0.0
        return sum(s.memory_percent for s in self.samples) / len(self.samples)

    @property
    def total_energy_mj(self) -> float:
        """Total estimated energy consumption in millijoules."""
        return sum(s.energy_estimate_mj for s in self.samples)


class MetricsCollector:
    """Collect system and application metrics."""

    def __init__(
        self,
        node_state: "NodeState",
        config: "SwarmConfig",
    ):
        self.node_state = node_state
        self.config = config
        self.state = MetricsState(
            samples=deque(maxlen=config.metrics.history_size)
        )

        self._running = False
        self._collect_task: asyncio.Task | None = None
        self._psutil_available = False
        self._process = None
        self._last_cpu_time = 0.0
        self._last_wall_time = time.time()

        # Try to import psutil
        try:
            import psutil

            self._psutil = psutil
            self._psutil_available = True
            self._process = psutil.Process()
        except ImportError:
            self._psutil = None

    async def start(self) -> None:
        """Start metrics collection."""
        if self._running or not self.config.metrics.enabled:
            return

        self._running = True
        self.state.start_time = datetime.now()

        if self._psutil_available:
            # Initialize CPU tracking
            self._last_cpu_time = self._process.cpu_times().user + self._process.cpu_times().system
            self._last_wall_time = time.time()

        loop = asyncio.get_event_loop()
        self._collect_task = loop.create_task(self._collection_loop())

    async def stop(self) -> None:
        """Stop metrics collection."""
        self._running = False

        if self._collect_task:
            self._collect_task.cancel()
            try:
                await self._collect_task
            except asyncio.CancelledError:
                pass

    async def _collection_loop(self) -> None:
        """Periodically collect metrics."""
        interval = self.config.metrics.collection_interval_ms / 1000.0

        while self._running:
            try:
                await asyncio.sleep(interval)
                sample = self._collect_sample()
                self.state.samples.append(sample)
                self._update_node_metrics(sample)
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    def _collect_sample(self) -> MetricSample:
        """Collect a single metric sample."""
        cpu_percent = 0.0
        memory_percent = 0.0
        memory_mb = 0.0
        energy_estimate = 0.0

        if self._psutil_available and self._process:
            try:
                # CPU usage
                cpu_percent = self._process.cpu_percent(interval=None)

                # Memory usage
                mem_info = self._process.memory_info()
                memory_mb = mem_info.rss / (1024 * 1024)
                memory_percent = self._process.memory_percent()

                # Energy estimation based on CPU time
                current_cpu_time = (
                    self._process.cpu_times().user + self._process.cpu_times().system
                )
                current_wall_time = time.time()

                cpu_time_delta = current_cpu_time - self._last_cpu_time
                wall_time_delta = current_wall_time - self._last_wall_time

                # Simple energy model: assume ~5W TDP for RPi 4, scale by CPU usage
                # Energy (mJ) = Power (W) * Time (s) * 1000
                if wall_time_delta > 0:
                    avg_power = 5.0 * (cpu_time_delta / wall_time_delta)
                    energy_estimate = avg_power * wall_time_delta * 1000

                self._last_cpu_time = current_cpu_time
                self._last_wall_time = current_wall_time

            except Exception:
                pass

        return MetricSample(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_mb=memory_mb,
            messages_sent=self.state.total_messages_sent,
            messages_received=self.state.total_messages_received,
            gossip_rounds=self.state.total_gossip_rounds,
            energy_estimate_mj=energy_estimate,
        )

    def _update_node_metrics(self, sample: MetricSample) -> None:
        """Update node state with latest metrics."""
        self.node_state.metrics = {
            "cpu_percent": round(sample.cpu_percent, 1),
            "memory_percent": round(sample.memory_percent, 1),
            "memory_mb": round(sample.memory_mb, 1),
            "messages_sent": sample.messages_sent,
            "messages_received": sample.messages_received,
            "gossip_rounds": sample.gossip_rounds,
            "energy_mj": round(sample.energy_estimate_mj, 2),
            "total_energy_mj": round(self.state.total_energy_mj, 2),
        }

    def record_message_sent(self) -> None:
        """Record a sent message."""
        self.state.total_messages_sent += 1

    def record_message_received(self) -> None:
        """Record a received message."""
        self.state.total_messages_received += 1

    def record_gossip_round(self) -> None:
        """Record a gossip round."""
        self.state.total_gossip_rounds += 1

    def get_summary(self) -> dict:
        """Get metrics summary."""
        latest = self.state.latest
        return {
            "cpu_percent": latest.cpu_percent if latest else 0.0,
            "memory_percent": latest.memory_percent if latest else 0.0,
            "memory_mb": latest.memory_mb if latest else 0.0,
            "avg_cpu": round(self.state.avg_cpu, 1),
            "avg_memory": round(self.state.avg_memory, 1),
            "messages_sent": self.state.total_messages_sent,
            "messages_received": self.state.total_messages_received,
            "gossip_rounds": self.state.total_gossip_rounds,
            "total_energy_mj": round(self.state.total_energy_mj, 2),
            "samples_collected": len(self.state.samples),
            "uptime_seconds": (datetime.now() - self.state.start_time).total_seconds(),
        }
