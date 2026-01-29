"""Adaptive gossip protocol for v0.2.0.

Dynamically adjusts gossip parameters based on:
- Network health and message loss
- Swarm size
- Energy constraints
- Activity level
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swarm_orchestrator.config import SwarmConfig
    from swarm_orchestrator.gossip.protocol import GossipProtocol
    from swarm_orchestrator.metrics.energy import EnergyCollector, PowerState


class GossipMode(str, Enum):
    """Gossip operating modes."""

    AGGRESSIVE = "aggressive"  # Fast propagation, higher energy
    NORMAL = "normal"  # Balanced operation
    CONSERVATIVE = "conservative"  # Slower, energy efficient
    EMERGENCY = "emergency"  # Minimal gossip, critical energy


@dataclass
class NetworkHealth:
    """Network health metrics for adaptation."""

    messages_sent: int = 0
    messages_received: int = 0
    messages_lost: int = 0  # Estimated from missing responses
    avg_latency_ms: float = 0.0
    peer_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def loss_rate(self) -> float:
        """Calculate message loss rate (0.0 to 1.0)."""
        total = self.messages_sent
        if total == 0:
            return 0.0
        return min(1.0, self.messages_lost / total)

    @property
    def health_score(self) -> float:
        """Calculate network health score (0-100)."""
        # Factors: loss rate, latency, peer count
        loss_penalty = self.loss_rate * 50
        latency_penalty = min(30, self.avg_latency_ms / 100)
        peer_bonus = min(20, self.peer_count * 2)
        return max(0, 100 - loss_penalty - latency_penalty + peer_bonus)


@dataclass
class AdaptiveParams:
    """Current adaptive gossip parameters."""

    interval_ms: int
    fanout: int
    ttl: int
    anti_entropy_interval_ms: int
    mode: GossipMode

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "interval_ms": self.interval_ms,
            "fanout": self.fanout,
            "ttl": self.ttl,
            "anti_entropy_interval_ms": self.anti_entropy_interval_ms,
            "mode": self.mode.value,
        }


class AdaptiveGossip:
    """Adaptive gossip controller that adjusts parameters dynamically."""

    def __init__(
        self,
        config: "SwarmConfig",
        gossip: "GossipProtocol",
        energy_collector: "EnergyCollector | None" = None,
    ):
        self.config = config
        self.gossip = gossip
        self.energy_collector = energy_collector

        # Base parameters from config
        self._base_interval_ms = config.gossip.interval_ms
        self._base_fanout = config.gossip.fanout
        self._base_ttl = config.gossip.ttl
        self._base_anti_entropy_ms = config.gossip.anti_entropy_interval_ms

        # Adaptive bounds
        self._min_interval_ms = config.adaptive_gossip.min_interval_ms
        self._max_interval_ms = config.adaptive_gossip.max_interval_ms
        self._min_fanout = 1
        self._max_fanout = config.adaptive_gossip.max_fanout

        # Current state
        self._mode = GossipMode.NORMAL
        self._current_params = AdaptiveParams(
            interval_ms=self._base_interval_ms,
            fanout=self._base_fanout,
            ttl=self._base_ttl,
            anti_entropy_interval_ms=self._base_anti_entropy_ms,
            mode=self._mode,
        )

        # Health tracking
        self._network_health = NetworkHealth()
        self._activity_window: list[datetime] = []
        self._activity_window_size = 60  # seconds

        # State
        self._running = False
        self._adapt_task: asyncio.Task | None = None

        # Callbacks for parameter changes
        self._on_params_changed: list[callable] = []

    def on_params_changed(self, callback: callable) -> None:
        """Register callback for when parameters change."""
        self._on_params_changed.append(callback)

    @property
    def current_params(self) -> AdaptiveParams:
        """Get current adaptive parameters."""
        return self._current_params

    @property
    def mode(self) -> GossipMode:
        """Get current gossip mode."""
        return self._mode

    @property
    def network_health(self) -> NetworkHealth:
        """Get network health metrics."""
        return self._network_health

    async def start(self) -> None:
        """Start adaptive gossip controller."""
        if self._running:
            return

        self._running = True

        loop = asyncio.get_event_loop()
        self._adapt_task = loop.create_task(self._adaptation_loop())

    async def stop(self) -> None:
        """Stop adaptive gossip controller."""
        self._running = False

        if self._adapt_task:
            self._adapt_task.cancel()
            try:
                await self._adapt_task
            except asyncio.CancelledError:
                pass

    async def _adaptation_loop(self) -> None:
        """Periodically adjust gossip parameters."""
        interval = self.config.adaptive_gossip.adaptation_interval_ms / 1000.0

        while self._running:
            try:
                await asyncio.sleep(interval)
                await self._adapt()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _adapt(self) -> None:
        """Perform one adaptation cycle."""
        # Gather inputs
        self._update_network_health()
        activity_level = self._calculate_activity_level()
        energy_state = self._get_energy_state()
        swarm_size = len(self.gossip.swarm_state.nodes)

        # Determine mode
        new_mode = self._determine_mode(energy_state, self._network_health)

        # Calculate new parameters
        new_params = self._calculate_params(
            mode=new_mode,
            activity_level=activity_level,
            health=self._network_health,
            swarm_size=swarm_size,
        )

        # Apply if changed
        if self._params_changed(new_params):
            self._current_params = new_params
            self._mode = new_mode
            await self._apply_params(new_params)

    def _update_network_health(self) -> None:
        """Update network health metrics."""
        # Get metrics from gossip protocol
        state = self.gossip.swarm_state

        self._network_health.peer_count = len(state.nodes) - 1
        self._network_health.last_updated = datetime.now()

        # Estimate loss from node staleness
        stale_count = sum(
            1 for n in state.nodes.values()
            if not n.is_alive(timeout_seconds=10.0)
        )
        self._network_health.messages_lost = stale_count

    def _calculate_activity_level(self) -> float:
        """Calculate recent activity level (0.0 to 1.0)."""
        # Clean old activity timestamps
        cutoff = datetime.now() - timedelta(seconds=self._activity_window_size)
        self._activity_window = [t for t in self._activity_window if t > cutoff]

        # Activity based on events per second
        if not self._activity_window:
            return 0.0

        events_per_second = len(self._activity_window) / self._activity_window_size
        # Normalize: assume 10 events/sec is max activity
        return min(1.0, events_per_second / 10.0)

    def _get_energy_state(self) -> "PowerState | None":
        """Get current energy/power state."""
        if self.energy_collector:
            sample = self.energy_collector.get_latest_sample()
            if sample:
                return sample.power_state
        return None

    def _determine_mode(
        self,
        energy_state: "PowerState | None",
        health: NetworkHealth,
    ) -> GossipMode:
        """Determine appropriate gossip mode."""
        from swarm_orchestrator.metrics.energy import PowerState

        # Energy-based mode selection
        if energy_state == PowerState.CRITICAL:
            return GossipMode.EMERGENCY
        if energy_state == PowerState.LOW_POWER:
            return GossipMode.CONSERVATIVE

        # Health-based mode selection
        if health.health_score < 50:
            return GossipMode.AGGRESSIVE  # Try to repair network
        if health.health_score > 90:
            return GossipMode.CONSERVATIVE  # Network is healthy, save energy

        return GossipMode.NORMAL

    def _calculate_params(
        self,
        mode: GossipMode,
        activity_level: float,
        health: NetworkHealth,
        swarm_size: int,
    ) -> AdaptiveParams:
        """Calculate optimal gossip parameters."""
        # Mode multipliers
        mode_configs = {
            GossipMode.AGGRESSIVE: {"interval": 0.5, "fanout": 1.5, "ttl": 1.0},
            GossipMode.NORMAL: {"interval": 1.0, "fanout": 1.0, "ttl": 1.0},
            GossipMode.CONSERVATIVE: {"interval": 2.0, "fanout": 0.7, "ttl": 1.0},
            GossipMode.EMERGENCY: {"interval": 4.0, "fanout": 0.5, "ttl": 0.5},
        }
        multipliers = mode_configs[mode]

        # Base interval adjusted by mode
        interval_ms = int(self._base_interval_ms * multipliers["interval"])

        # Adjust interval based on activity (more active = faster)
        activity_factor = 1.0 - (activity_level * 0.3)  # Up to 30% faster
        interval_ms = int(interval_ms * activity_factor)

        # Adjust interval based on swarm size (larger = slower)
        if swarm_size > 10:
            size_factor = 1.0 + (swarm_size - 10) * 0.05  # 5% slower per node over 10
            interval_ms = int(interval_ms * min(2.0, size_factor))

        # Clamp interval
        interval_ms = max(self._min_interval_ms, min(self._max_interval_ms, interval_ms))

        # Calculate fanout
        fanout = int(self._base_fanout * multipliers["fanout"])
        # Larger swarms need larger fanout for coverage
        if swarm_size > 5:
            fanout = max(fanout, min(self._max_fanout, swarm_size // 3))
        fanout = max(self._min_fanout, min(self._max_fanout, fanout))

        # TTL based on swarm size and mode
        ttl = max(1, int(self._base_ttl * multipliers["ttl"]))
        if swarm_size > 20:
            ttl = min(5, ttl + 1)  # Increase TTL for larger swarms

        # Anti-entropy interval (inversely related to gossip speed)
        anti_entropy_ms = int(self._base_anti_entropy_ms * (interval_ms / self._base_interval_ms))
        anti_entropy_ms = max(5000, min(60000, anti_entropy_ms))

        return AdaptiveParams(
            interval_ms=interval_ms,
            fanout=fanout,
            ttl=ttl,
            anti_entropy_interval_ms=anti_entropy_ms,
            mode=mode,
        )

    def _params_changed(self, new_params: AdaptiveParams) -> bool:
        """Check if parameters have changed significantly."""
        old = self._current_params
        return (
            abs(new_params.interval_ms - old.interval_ms) > 100
            or new_params.fanout != old.fanout
            or new_params.ttl != old.ttl
            or new_params.mode != old.mode
        )

    async def _apply_params(self, params: AdaptiveParams) -> None:
        """Apply new parameters to gossip protocol."""
        # Update config (gossip protocol reads from config)
        self.config.gossip.interval_ms = params.interval_ms
        self.config.gossip.fanout = params.fanout
        self.config.gossip.ttl = params.ttl
        self.config.gossip.anti_entropy_interval_ms = params.anti_entropy_interval_ms

        # Notify listeners
        for callback in self._on_params_changed:
            try:
                await callback(params)
            except Exception:
                pass

    def record_activity(self) -> None:
        """Record an activity event (message sent/received)."""
        self._activity_window.append(datetime.now())

    def record_message_sent(self) -> None:
        """Record a sent message."""
        self._network_health.messages_sent += 1
        self.record_activity()

    def record_message_received(self) -> None:
        """Record a received message."""
        self._network_health.messages_received += 1
        self.record_activity()

    def get_summary(self) -> dict:
        """Get adaptive gossip summary."""
        return {
            "mode": self._mode.value,
            "params": self._current_params.to_dict(),
            "network_health": {
                "score": round(self._network_health.health_score, 1),
                "loss_rate": round(self._network_health.loss_rate * 100, 1),
                "peer_count": self._network_health.peer_count,
                "avg_latency_ms": round(self._network_health.avg_latency_ms, 1),
            },
            "activity_level": round(self._calculate_activity_level() * 100, 1),
        }
