"""Core Pydantic v2 models for swarm orchestration."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class NodeRole(str, Enum):
    """Role of a node in the swarm."""

    LEADER = "leader"
    FOLLOWER = "follower"
    CANDIDATE = "candidate"


class NodeStatus(str, Enum):
    """Health status of a node."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNREACHABLE = "unreachable"


class DeviceClass(str, Enum):
    """Device capability class."""

    FULL = "full"  # RPi 4 - can be leader
    STANDARD = "standard"  # RPi Zero, ESP32-S3
    MINIMAL = "minimal"  # ESP32 - observer only


class NodeState(BaseModel):
    """State of a single node in the swarm."""

    node_id: UUID = Field(default_factory=uuid4)
    hostname: str
    role: NodeRole = NodeRole.FOLLOWER
    status: NodeStatus = NodeStatus.HEALTHY
    device_class: DeviceClass = DeviceClass.STANDARD
    ip_address: str
    gossip_port: int = 5555
    heartbeat_count: int = 0
    last_seen: datetime = Field(default_factory=datetime.now)
    term: int = 0
    voted_for: UUID | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)

    def can_be_leader(self) -> bool:
        """Check if this node can become a leader."""
        return self.device_class in (DeviceClass.FULL, DeviceClass.STANDARD)

    def is_alive(self, timeout_seconds: float = 5.0) -> bool:
        """Check if node has been seen recently."""
        elapsed = (datetime.now() - self.last_seen).total_seconds()
        return elapsed < timeout_seconds

    def touch(self) -> None:
        """Update last_seen timestamp."""
        self.last_seen = datetime.now()

    def increment_heartbeat(self) -> None:
        """Increment heartbeat counter and touch."""
        self.heartbeat_count += 1
        self.touch()


class Message(BaseModel):
    """Base message for gossip protocol."""

    message_id: UUID = Field(default_factory=uuid4)
    sender_id: UUID
    message_type: str  # "announce", "gossip", "heartbeat", "vote_request", "vote_response"
    payload: dict[str, Any] = Field(default_factory=dict)
    ttl: int = 3
    timestamp: datetime = Field(default_factory=datetime.now)

    def decrement_ttl(self) -> "Message":
        """Return a copy with decremented TTL."""
        return self.model_copy(update={"ttl": self.ttl - 1})

    def is_expired(self) -> bool:
        """Check if message TTL is exhausted."""
        return self.ttl <= 0


class SwarmState(BaseModel):
    """State of the entire swarm."""

    swarm_id: UUID = Field(default_factory=uuid4)
    swarm_name: str = "default"
    nodes: dict[str, NodeState] = Field(default_factory=dict)
    leader_id: UUID | None = None
    current_term: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def add_node(self, node: NodeState) -> None:
        """Add or update a node in the swarm."""
        self.nodes[str(node.node_id)] = node
        self.updated_at = datetime.now()

    def remove_node(self, node_id: UUID) -> None:
        """Remove a node from the swarm."""
        self.nodes.pop(str(node_id), None)
        if self.leader_id == node_id:
            self.leader_id = None
        self.updated_at = datetime.now()

    def get_node(self, node_id: UUID) -> NodeState | None:
        """Get a node by ID."""
        return self.nodes.get(str(node_id))

    def get_leader(self) -> NodeState | None:
        """Get the current leader node."""
        if self.leader_id:
            return self.get_node(self.leader_id)
        return None

    def set_leader(self, node_id: UUID) -> None:
        """Set the swarm leader."""
        node = self.get_node(node_id)
        if node:
            # Demote current leader
            if self.leader_id and self.leader_id != node_id:
                old_leader = self.get_node(self.leader_id)
                if old_leader:
                    old_leader.role = NodeRole.FOLLOWER

            # Promote new leader
            node.role = NodeRole.LEADER
            self.leader_id = node_id
            self.updated_at = datetime.now()

    def get_healthy_nodes(self) -> list[NodeState]:
        """Get all healthy nodes."""
        return [n for n in self.nodes.values() if n.status == NodeStatus.HEALTHY]

    def get_alive_nodes(self, timeout_seconds: float = 5.0) -> list[NodeState]:
        """Get all nodes that have been seen recently."""
        return [n for n in self.nodes.values() if n.is_alive(timeout_seconds)]

    def get_eligible_leaders(self) -> list[NodeState]:
        """Get nodes that can become leader."""
        return [
            n
            for n in self.nodes.values()
            if n.can_be_leader() and n.status == NodeStatus.HEALTHY
        ]

    @property
    def node_count(self) -> int:
        """Total number of nodes."""
        return len(self.nodes)

    @property
    def healthy_count(self) -> int:
        """Number of healthy nodes."""
        return len(self.get_healthy_nodes())


class VoteRequest(BaseModel):
    """Vote request for leader election."""

    candidate_id: UUID
    term: int
    last_heartbeat_count: int = 0


class VoteResponse(BaseModel):
    """Vote response for leader election."""

    voter_id: UUID
    term: int
    vote_granted: bool
    reason: str = ""
