"""Gossip message types."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Types of gossip messages."""

    ANNOUNCE = "announce"  # Node announcing itself
    GOSSIP = "gossip"  # State propagation
    HEARTBEAT = "heartbeat"  # Leader heartbeat
    VOTE_REQUEST = "vote_request"  # Request vote for election
    VOTE_RESPONSE = "vote_response"  # Response to vote request
    SYNC_REQUEST = "sync_request"  # Anti-entropy sync request
    SYNC_RESPONSE = "sync_response"  # Anti-entropy sync response
    LEAVE = "leave"  # Node leaving the swarm


class GossipMessage(BaseModel):
    """A message in the gossip protocol."""

    message_id: UUID = Field(default_factory=uuid4)
    sender_id: UUID
    sender_address: str  # ip:port for direct replies
    message_type: MessageType
    payload: dict[str, Any] = Field(default_factory=dict)
    ttl: int = 3
    timestamp: datetime = Field(default_factory=datetime.now)
    term: int = 0  # Raft term for consensus messages

    def to_bytes(self) -> bytes:
        """Serialize message to bytes for transport."""
        return self.model_dump_json().encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "GossipMessage":
        """Deserialize message from bytes."""
        return cls.model_validate_json(data.decode("utf-8"))

    def decrement_ttl(self) -> "GossipMessage":
        """Return a copy with decremented TTL."""
        return self.model_copy(update={"ttl": self.ttl - 1})

    def is_expired(self) -> bool:
        """Check if message TTL is exhausted."""
        return self.ttl <= 0

    def is_stale(self, max_age_seconds: float = 30.0) -> bool:
        """Check if message is too old."""
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > max_age_seconds


class AnnouncePayload(BaseModel):
    """Payload for ANNOUNCE messages."""

    hostname: str
    device_class: str
    gossip_port: int


class HeartbeatPayload(BaseModel):
    """Payload for HEARTBEAT messages."""

    leader_id: UUID
    term: int
    heartbeat_count: int
    node_count: int


class VoteRequestPayload(BaseModel):
    """Payload for VOTE_REQUEST messages."""

    candidate_id: UUID
    term: int
    last_heartbeat_count: int


class VoteResponsePayload(BaseModel):
    """Payload for VOTE_RESPONSE messages."""

    voter_id: UUID
    term: int
    vote_granted: bool
    reason: str = ""


class GossipPayload(BaseModel):
    """Payload for GOSSIP messages (state propagation)."""

    nodes: dict[str, dict[str, Any]]  # Serialized NodeState objects
    leader_id: str | None
    term: int


class SyncRequestPayload(BaseModel):
    """Payload for SYNC_REQUEST messages."""

    known_nodes: list[str]  # List of node IDs this node knows about
    term: int


class SyncResponsePayload(BaseModel):
    """Payload for SYNC_RESPONSE messages."""

    nodes: dict[str, dict[str, Any]]  # Full node states
    leader_id: str | None
    term: int
