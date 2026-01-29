"""Tests for gossip protocol."""

from datetime import datetime
from uuid import uuid4

import pytest

from swarm_orchestrator.gossip.message import (
    AnnouncePayload,
    GossipMessage,
    GossipPayload,
    HeartbeatPayload,
    MessageType,
    VoteRequestPayload,
    VoteResponsePayload,
)


class TestMessageType:
    """Tests for message types."""

    def test_message_types(self):
        """Test all message types exist."""
        assert MessageType.ANNOUNCE.value == "announce"
        assert MessageType.GOSSIP.value == "gossip"
        assert MessageType.HEARTBEAT.value == "heartbeat"
        assert MessageType.VOTE_REQUEST.value == "vote_request"
        assert MessageType.VOTE_RESPONSE.value == "vote_response"
        assert MessageType.SYNC_REQUEST.value == "sync_request"
        assert MessageType.SYNC_RESPONSE.value == "sync_response"
        assert MessageType.LEAVE.value == "leave"


class TestGossipMessage:
    """Tests for GossipMessage model."""

    def test_create_message(self):
        """Test creating a gossip message."""
        sender_id = uuid4()
        msg = GossipMessage(
            sender_id=sender_id,
            sender_address="192.168.1.1:5555",
            message_type=MessageType.ANNOUNCE,
            payload={"hostname": "test"},
        )

        assert msg.sender_id == sender_id
        assert msg.sender_address == "192.168.1.1:5555"
        assert msg.message_type == MessageType.ANNOUNCE
        assert msg.payload == {"hostname": "test"}
        assert msg.ttl == 3
        assert msg.term == 0

    def test_serialization(self):
        """Test message serialization round-trip."""
        sender_id = uuid4()
        original = GossipMessage(
            sender_id=sender_id,
            sender_address="192.168.1.1:5555",
            message_type=MessageType.GOSSIP,
            payload={"test": "data"},
            ttl=2,
            term=5,
        )

        # Serialize and deserialize
        data = original.to_bytes()
        restored = GossipMessage.from_bytes(data)

        assert restored.sender_id == original.sender_id
        assert restored.sender_address == original.sender_address
        assert restored.message_type == original.message_type
        assert restored.payload == original.payload
        assert restored.ttl == original.ttl
        assert restored.term == original.term

    def test_ttl_decrement(self):
        """Test TTL decrement."""
        msg = GossipMessage(
            sender_id=uuid4(),
            sender_address="192.168.1.1:5555",
            message_type=MessageType.ANNOUNCE,
            ttl=3,
        )

        msg2 = msg.decrement_ttl()
        assert msg2.ttl == 2
        assert msg.ttl == 3  # Original unchanged

    def test_is_expired(self):
        """Test expiration check."""
        msg = GossipMessage(
            sender_id=uuid4(),
            sender_address="192.168.1.1:5555",
            message_type=MessageType.ANNOUNCE,
            ttl=1,
        )
        assert msg.is_expired() is False

        msg2 = msg.decrement_ttl()
        assert msg2.is_expired() is True

    def test_is_stale(self):
        """Test stale message check."""
        msg = GossipMessage(
            sender_id=uuid4(),
            sender_address="192.168.1.1:5555",
            message_type=MessageType.ANNOUNCE,
        )

        # Fresh message
        assert msg.is_stale(max_age_seconds=30.0) is False

        # Old message
        from datetime import timedelta
        msg.timestamp = datetime.now() - timedelta(seconds=60)
        assert msg.is_stale(max_age_seconds=30.0) is True


class TestPayloads:
    """Tests for message payload models."""

    def test_announce_payload(self):
        """Test announce payload."""
        payload = AnnouncePayload(
            hostname="test-node",
            device_class="standard",
            gossip_port=5555,
        )

        assert payload.hostname == "test-node"
        assert payload.device_class == "standard"
        assert payload.gossip_port == 5555

    def test_heartbeat_payload(self):
        """Test heartbeat payload."""
        leader_id = uuid4()
        payload = HeartbeatPayload(
            leader_id=leader_id,
            term=5,
            heartbeat_count=100,
            node_count=3,
        )

        assert payload.leader_id == leader_id
        assert payload.term == 5
        assert payload.heartbeat_count == 100
        assert payload.node_count == 3

    def test_vote_request_payload(self):
        """Test vote request payload."""
        candidate_id = uuid4()
        payload = VoteRequestPayload(
            candidate_id=candidate_id,
            term=5,
            last_heartbeat_count=50,
        )

        assert payload.candidate_id == candidate_id
        assert payload.term == 5
        assert payload.last_heartbeat_count == 50

    def test_vote_response_payload(self):
        """Test vote response payload."""
        voter_id = uuid4()
        payload = VoteResponsePayload(
            voter_id=voter_id,
            term=5,
            vote_granted=True,
            reason="",
        )

        assert payload.voter_id == voter_id
        assert payload.term == 5
        assert payload.vote_granted is True

    def test_gossip_payload(self):
        """Test gossip payload."""
        payload = GossipPayload(
            nodes={"node1": {"hostname": "test"}},
            leader_id="node1",
            term=3,
        )

        assert "node1" in payload.nodes
        assert payload.leader_id == "node1"
        assert payload.term == 3


class TestMessagePayloadIntegration:
    """Test message with payload integration."""

    def test_announce_message(self):
        """Test creating announce message with payload."""
        sender_id = uuid4()
        payload = AnnouncePayload(
            hostname="test-node",
            device_class="full",
            gossip_port=5555,
        )

        msg = GossipMessage(
            sender_id=sender_id,
            sender_address="192.168.1.1:5555",
            message_type=MessageType.ANNOUNCE,
            payload=payload.model_dump(),
        )

        # Round trip
        data = msg.to_bytes()
        restored = GossipMessage.from_bytes(data)

        # Extract payload
        restored_payload = AnnouncePayload(**restored.payload)
        assert restored_payload.hostname == "test-node"
        assert restored_payload.device_class == "full"

    def test_heartbeat_message(self):
        """Test creating heartbeat message."""
        sender_id = uuid4()
        payload = HeartbeatPayload(
            leader_id=sender_id,
            term=10,
            heartbeat_count=500,
            node_count=5,
        )

        msg = GossipMessage(
            sender_id=sender_id,
            sender_address="192.168.1.1:5555",
            message_type=MessageType.HEARTBEAT,
            payload=payload.model_dump(),
            term=10,
            ttl=1,  # Heartbeats don't propagate
        )

        assert msg.message_type == MessageType.HEARTBEAT
        assert msg.term == 10
        assert msg.ttl == 1
