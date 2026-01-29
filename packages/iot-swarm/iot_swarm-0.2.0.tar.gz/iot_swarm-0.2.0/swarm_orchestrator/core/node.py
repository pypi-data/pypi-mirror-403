"""Node lifecycle management."""

import asyncio
import platform
import socket
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from swarm_orchestrator.config import SwarmConfig, load_config
from swarm_orchestrator.gossip.protocol import GossipProtocol
from swarm_orchestrator.models import DeviceClass, NodeRole, NodeState, NodeStatus, SwarmState

if TYPE_CHECKING:
    from swarm_orchestrator.consensus.election import LeaderElection
    from swarm_orchestrator.gossip.adaptive import AdaptiveGossip
    from swarm_orchestrator.metrics.collector import MetricsCollector
    from swarm_orchestrator.metrics.energy import EnergyCollector


class Node:
    """A single node in the swarm."""

    def __init__(
        self,
        config: SwarmConfig | None = None,
        name: str | None = None,
        node_id: UUID | None = None,
    ):
        self.config = config or load_config()
        self._node_id = node_id or uuid4()
        self._name = name or self.config.node.name or self._generate_name()

        # Initialize node state
        self.state = NodeState(
            node_id=self._node_id,
            hostname=self._name,
            role=NodeRole.FOLLOWER,
            status=NodeStatus.HEALTHY,
            device_class=DeviceClass(self.config.node.device_class),
            ip_address=self._get_local_ip(),
            gossip_port=self.config.network.gossip_port,
        )

        # Initialize swarm state
        self.swarm_state = SwarmState(swarm_name="default")
        self.swarm_state.add_node(self.state)

        # Protocol components (initialized on start)
        self._gossip: GossipProtocol | None = None
        self._election: "LeaderElection | None" = None
        self._metrics: "MetricsCollector | None" = None
        self._energy: "EnergyCollector | None" = None
        self._adaptive_gossip: "AdaptiveGossip | None" = None

        # Runtime state
        self._running = False
        self._started_at: datetime | None = None

    @property
    def node_id(self) -> UUID:
        """Get this node's ID."""
        return self._node_id

    @property
    def name(self) -> str:
        """Get this node's name."""
        return self._name

    @property
    def is_leader(self) -> bool:
        """Check if this node is the leader."""
        return self.state.role == NodeRole.LEADER

    @property
    def is_running(self) -> bool:
        """Check if node is running."""
        return self._running

    @property
    def uptime(self) -> float:
        """Get node uptime in seconds."""
        if self._started_at:
            return (datetime.now() - self._started_at).total_seconds()
        return 0.0

    def _generate_name(self) -> str:
        """Generate a node name from hostname."""
        hostname = platform.node()
        short_id = str(self._node_id)[:8]
        return f"{hostname}-{short_id}"

    def _get_local_ip(self) -> str:
        """Get the local IP address."""
        try:
            # Create a socket to determine the outgoing interface
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    async def start(self) -> None:
        """Start the node and join the swarm."""
        if self._running:
            return

        self._running = True
        self._started_at = datetime.now()
        self.state.status = NodeStatus.HEALTHY
        self.state.touch()

        # Initialize gossip protocol
        self._gossip = GossipProtocol(
            node_state=self.state,
            swarm_state=self.swarm_state,
            config=self.config,
        )

        # Set up gossip callbacks
        self._gossip.on_node_discovered(self._on_node_discovered)
        self._gossip.on_node_updated(self._on_node_updated)

        # Start gossip
        await self._gossip.start()

        # Initialize and start leader election
        from swarm_orchestrator.consensus.election import LeaderElection

        self._election = LeaderElection(
            node_state=self.state,
            swarm_state=self.swarm_state,
            config=self.config,
            gossip=self._gossip,
        )
        await self._election.start()

        # Initialize metrics collector if available
        try:
            from swarm_orchestrator.metrics.collector import MetricsCollector

            self._metrics = MetricsCollector(
                node_state=self.state,
                config=self.config,
            )
            await self._metrics.start()
        except ImportError:
            # psutil not installed
            pass

        # Initialize energy collector (v0.2.0)
        if self.config.energy.enabled:
            try:
                from swarm_orchestrator.metrics.energy import EnergyCollector

                self._energy = EnergyCollector(
                    node_state=self.state,
                    config=self.config,
                )
                await self._energy.start()
            except Exception:
                pass

        # Initialize adaptive gossip (v0.2.0)
        if self.config.adaptive_gossip.enabled:
            try:
                from swarm_orchestrator.gossip.adaptive import AdaptiveGossip

                self._adaptive_gossip = AdaptiveGossip(
                    config=self.config,
                    gossip=self._gossip,
                    energy_collector=self._energy,
                )
                await self._adaptive_gossip.start()
            except Exception:
                pass

    async def stop(self) -> None:
        """Stop the node and leave the swarm."""
        if not self._running:
            return

        self._running = False
        self.state.status = NodeStatus.UNREACHABLE

        # Stop components in reverse order
        if self._adaptive_gossip:
            await self._adaptive_gossip.stop()

        if self._energy:
            await self._energy.stop()

        if self._metrics:
            await self._metrics.stop()

        if self._election:
            await self._election.stop()

        if self._gossip:
            await self._gossip.stop()

    async def _on_node_discovered(self, node: NodeState) -> None:
        """Handle new node discovery."""
        # Trigger election check if we have no leader
        if self._election and self.swarm_state.leader_id is None:
            await self._election.check_election()

    async def _on_node_updated(self, node: NodeState) -> None:
        """Handle node state update."""
        pass

    def get_status(self) -> dict:
        """Get current node status as a dictionary."""
        status = {
            "node_id": str(self.node_id),
            "name": self.name,
            "role": self.state.role.value,
            "status": self.state.status.value,
            "device_class": self.state.device_class.value,
            "ip_address": self.state.ip_address,
            "gossip_port": self.state.gossip_port,
            "uptime": self.uptime,
            "is_leader": self.is_leader,
            "swarm": {
                "node_count": self.swarm_state.node_count,
                "healthy_count": self.swarm_state.healthy_count,
                "leader_id": str(self.swarm_state.leader_id) if self.swarm_state.leader_id else None,
                "term": self.swarm_state.current_term,
            },
            "metrics": self.state.metrics,
        }

        # Add energy metrics (v0.2.0)
        if self._energy:
            status["energy"] = self._energy.get_summary()

        # Add adaptive gossip status (v0.2.0)
        if self._adaptive_gossip:
            status["adaptive_gossip"] = self._adaptive_gossip.get_summary()

        return status

    @property
    def energy_collector(self) -> "EnergyCollector | None":
        """Get the energy collector."""
        return self._energy

    @property
    def adaptive_gossip(self) -> "AdaptiveGossip | None":
        """Get the adaptive gossip controller."""
        return self._adaptive_gossip

    def save_state(self, path: Path | None = None) -> None:
        """Save node state to disk."""
        save_path = path or (self.config.node.data_dir / "node_state.json")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(self.state.model_dump_json(indent=2))

    @classmethod
    def load_state(cls, path: Path, config: SwarmConfig | None = None) -> "Node":
        """Load node from saved state."""
        state = NodeState.model_validate_json(path.read_text())
        node = cls(config=config, name=state.hostname, node_id=state.node_id)
        node.state = state
        return node
