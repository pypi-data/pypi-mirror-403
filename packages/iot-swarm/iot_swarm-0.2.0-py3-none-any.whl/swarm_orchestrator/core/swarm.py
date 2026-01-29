"""Swarm orchestration."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from swarm_orchestrator.models import NodeRole, NodeState, NodeStatus, SwarmState

if TYPE_CHECKING:
    from swarm_orchestrator.core.node import Node


class Swarm:
    """High-level swarm orchestration."""

    def __init__(self, local_node: "Node"):
        self.local_node = local_node
        self._state = local_node.swarm_state

    @property
    def state(self) -> SwarmState:
        """Get swarm state."""
        return self._state

    @property
    def node_count(self) -> int:
        """Total number of nodes in swarm."""
        return self._state.node_count

    @property
    def healthy_count(self) -> int:
        """Number of healthy nodes."""
        return self._state.healthy_count

    @property
    def leader(self) -> NodeState | None:
        """Get the current leader."""
        return self._state.get_leader()

    @property
    def is_local_leader(self) -> bool:
        """Check if local node is the leader."""
        return self.local_node.is_leader

    def get_nodes(self) -> list[NodeState]:
        """Get all nodes in the swarm."""
        return list(self._state.nodes.values())

    def get_node(self, node_id: UUID) -> NodeState | None:
        """Get a specific node."""
        return self._state.get_node(node_id)

    def get_healthy_nodes(self) -> list[NodeState]:
        """Get all healthy nodes."""
        return self._state.get_healthy_nodes()

    def get_alive_nodes(self, timeout_seconds: float = 5.0) -> list[NodeState]:
        """Get nodes that have been seen recently."""
        return self._state.get_alive_nodes(timeout_seconds)

    def get_followers(self) -> list[NodeState]:
        """Get all follower nodes."""
        return [n for n in self._state.nodes.values() if n.role == NodeRole.FOLLOWER]

    def get_unreachable_nodes(self) -> list[NodeState]:
        """Get nodes marked as unreachable."""
        return [n for n in self._state.nodes.values() if n.status == NodeStatus.UNREACHABLE]

    def mark_node_unhealthy(self, node_id: UUID) -> None:
        """Mark a node as unhealthy."""
        node = self._state.get_node(node_id)
        if node:
            node.status = NodeStatus.DEGRADED
            self._state.updated_at = datetime.now()

    def mark_node_unreachable(self, node_id: UUID) -> None:
        """Mark a node as unreachable."""
        node = self._state.get_node(node_id)
        if node:
            node.status = NodeStatus.UNREACHABLE
            self._state.updated_at = datetime.now()

    def get_status_summary(self) -> dict:
        """Get a summary of swarm status."""
        nodes = self.get_nodes()
        by_role = {role: 0 for role in NodeRole}
        by_status = {status: 0 for status in NodeStatus}
        by_class = {}

        for node in nodes:
            by_role[node.role] += 1
            by_status[node.status] += 1
            by_class[node.device_class.value] = by_class.get(node.device_class.value, 0) + 1

        return {
            "swarm_id": str(self._state.swarm_id),
            "swarm_name": self._state.swarm_name,
            "node_count": len(nodes),
            "healthy_count": by_status[NodeStatus.HEALTHY],
            "degraded_count": by_status[NodeStatus.DEGRADED],
            "unreachable_count": by_status[NodeStatus.UNREACHABLE],
            "leader_count": by_role[NodeRole.LEADER],
            "follower_count": by_role[NodeRole.FOLLOWER],
            "candidate_count": by_role[NodeRole.CANDIDATE],
            "by_device_class": by_class,
            "leader_id": str(self._state.leader_id) if self._state.leader_id else None,
            "current_term": self._state.current_term,
            "local_node_id": str(self.local_node.node_id),
            "is_local_leader": self.is_local_leader,
        }

    def get_node_table_data(self) -> list[dict]:
        """Get node data formatted for table display."""
        nodes = sorted(
            self.get_nodes(),
            key=lambda n: (n.role != NodeRole.LEADER, n.hostname),
        )

        return [
            {
                "node_id": str(n.node_id)[:8],
                "hostname": n.hostname,
                "role": n.role.value,
                "status": n.status.value,
                "device_class": n.device_class.value,
                "ip_address": f"{n.ip_address}:{n.gossip_port}",
                "last_seen": n.last_seen.strftime("%H:%M:%S"),
                "heartbeats": n.heartbeat_count,
                "is_local": n.node_id == self.local_node.node_id,
            }
            for n in nodes
        ]
