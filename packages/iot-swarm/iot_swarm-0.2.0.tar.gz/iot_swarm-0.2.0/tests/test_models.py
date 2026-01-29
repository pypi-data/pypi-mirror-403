"""Tests for core models."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from swarm_orchestrator.models import (
    DeviceClass,
    Message,
    NodeRole,
    NodeState,
    NodeStatus,
    SwarmState,
    VoteRequest,
    VoteResponse,
)


class TestNodeState:
    """Tests for NodeState model."""

    def test_create_node_state(self):
        """Test creating a node state."""
        node = NodeState(
            hostname="test-node",
            ip_address="192.168.1.100",
        )

        assert node.hostname == "test-node"
        assert node.ip_address == "192.168.1.100"
        assert node.role == NodeRole.FOLLOWER
        assert node.status == NodeStatus.HEALTHY
        assert node.device_class == DeviceClass.STANDARD
        assert node.gossip_port == 5555
        assert node.heartbeat_count == 0

    def test_can_be_leader(self):
        """Test leader eligibility."""
        full_node = NodeState(
            hostname="full",
            ip_address="192.168.1.1",
            device_class=DeviceClass.FULL,
        )
        assert full_node.can_be_leader() is True

        standard_node = NodeState(
            hostname="standard",
            ip_address="192.168.1.2",
            device_class=DeviceClass.STANDARD,
        )
        assert standard_node.can_be_leader() is True

        minimal_node = NodeState(
            hostname="minimal",
            ip_address="192.168.1.3",
            device_class=DeviceClass.MINIMAL,
        )
        assert minimal_node.can_be_leader() is False

    def test_is_alive(self):
        """Test node liveness check."""
        node = NodeState(
            hostname="test",
            ip_address="192.168.1.1",
        )

        # Just created, should be alive
        assert node.is_alive(timeout_seconds=5.0) is True

        # Simulate old last_seen
        node.last_seen = datetime.now() - timedelta(seconds=10)
        assert node.is_alive(timeout_seconds=5.0) is False

    def test_touch(self):
        """Test touching a node."""
        node = NodeState(
            hostname="test",
            ip_address="192.168.1.1",
        )
        old_time = node.last_seen

        node.last_seen = datetime.now() - timedelta(seconds=10)
        node.touch()

        assert node.last_seen > old_time

    def test_increment_heartbeat(self):
        """Test incrementing heartbeat."""
        node = NodeState(
            hostname="test",
            ip_address="192.168.1.1",
        )

        assert node.heartbeat_count == 0
        node.increment_heartbeat()
        assert node.heartbeat_count == 1
        node.increment_heartbeat()
        assert node.heartbeat_count == 2


class TestMessage:
    """Tests for Message model."""

    def test_create_message(self):
        """Test creating a message."""
        sender_id = uuid4()
        msg = Message(
            sender_id=sender_id,
            message_type="gossip",
            payload={"key": "value"},
        )

        assert msg.sender_id == sender_id
        assert msg.message_type == "gossip"
        assert msg.payload == {"key": "value"}
        assert msg.ttl == 3

    def test_decrement_ttl(self):
        """Test TTL decrement."""
        msg = Message(
            sender_id=uuid4(),
            message_type="gossip",
            ttl=3,
        )

        msg2 = msg.decrement_ttl()
        assert msg2.ttl == 2
        assert msg.ttl == 3  # Original unchanged

    def test_is_expired(self):
        """Test expiration check."""
        msg = Message(
            sender_id=uuid4(),
            message_type="gossip",
            ttl=1,
        )
        assert msg.is_expired() is False

        msg2 = msg.decrement_ttl()
        assert msg2.is_expired() is True


class TestSwarmState:
    """Tests for SwarmState model."""

    def test_create_swarm_state(self):
        """Test creating swarm state."""
        swarm = SwarmState(swarm_name="test-swarm")

        assert swarm.swarm_name == "test-swarm"
        assert swarm.node_count == 0
        assert swarm.leader_id is None
        assert swarm.current_term == 0

    def test_add_node(self):
        """Test adding nodes."""
        swarm = SwarmState()
        node = NodeState(hostname="test", ip_address="192.168.1.1")

        swarm.add_node(node)

        assert swarm.node_count == 1
        assert swarm.get_node(node.node_id) == node

    def test_remove_node(self):
        """Test removing nodes."""
        swarm = SwarmState()
        node = NodeState(hostname="test", ip_address="192.168.1.1")

        swarm.add_node(node)
        assert swarm.node_count == 1

        swarm.remove_node(node.node_id)
        assert swarm.node_count == 0
        assert swarm.get_node(node.node_id) is None

    def test_set_leader(self):
        """Test setting leader."""
        swarm = SwarmState()
        node1 = NodeState(hostname="node1", ip_address="192.168.1.1")
        node2 = NodeState(hostname="node2", ip_address="192.168.1.2")

        swarm.add_node(node1)
        swarm.add_node(node2)

        swarm.set_leader(node1.node_id)
        assert swarm.leader_id == node1.node_id
        assert node1.role == NodeRole.LEADER

        # Change leader
        swarm.set_leader(node2.node_id)
        assert swarm.leader_id == node2.node_id
        assert node2.role == NodeRole.LEADER
        assert node1.role == NodeRole.FOLLOWER

    def test_get_healthy_nodes(self):
        """Test getting healthy nodes."""
        swarm = SwarmState()

        healthy = NodeState(
            hostname="healthy",
            ip_address="192.168.1.1",
            status=NodeStatus.HEALTHY,
        )
        degraded = NodeState(
            hostname="degraded",
            ip_address="192.168.1.2",
            status=NodeStatus.DEGRADED,
        )
        unreachable = NodeState(
            hostname="unreachable",
            ip_address="192.168.1.3",
            status=NodeStatus.UNREACHABLE,
        )

        swarm.add_node(healthy)
        swarm.add_node(degraded)
        swarm.add_node(unreachable)

        healthy_nodes = swarm.get_healthy_nodes()
        assert len(healthy_nodes) == 1
        assert healthy_nodes[0].hostname == "healthy"

    def test_get_eligible_leaders(self):
        """Test getting eligible leaders."""
        swarm = SwarmState()

        full = NodeState(
            hostname="full",
            ip_address="192.168.1.1",
            device_class=DeviceClass.FULL,
        )
        minimal = NodeState(
            hostname="minimal",
            ip_address="192.168.1.2",
            device_class=DeviceClass.MINIMAL,
        )
        unhealthy_full = NodeState(
            hostname="unhealthy",
            ip_address="192.168.1.3",
            device_class=DeviceClass.FULL,
            status=NodeStatus.DEGRADED,
        )

        swarm.add_node(full)
        swarm.add_node(minimal)
        swarm.add_node(unhealthy_full)

        eligible = swarm.get_eligible_leaders()
        assert len(eligible) == 1
        assert eligible[0].hostname == "full"


class TestVoteModels:
    """Tests for vote request/response models."""

    def test_vote_request(self):
        """Test vote request."""
        candidate_id = uuid4()
        req = VoteRequest(
            candidate_id=candidate_id,
            term=5,
            last_heartbeat_count=10,
        )

        assert req.candidate_id == candidate_id
        assert req.term == 5
        assert req.last_heartbeat_count == 10

    def test_vote_response(self):
        """Test vote response."""
        voter_id = uuid4()
        resp = VoteResponse(
            voter_id=voter_id,
            term=5,
            vote_granted=True,
            reason="",
        )

        assert resp.voter_id == voter_id
        assert resp.term == 5
        assert resp.vote_granted is True
