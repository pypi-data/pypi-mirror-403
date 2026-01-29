"""Gossip protocol implementation."""

import asyncio
import random
from collections import OrderedDict
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from swarm_orchestrator.gossip.message import (
    AnnouncePayload,
    GossipMessage,
    GossipPayload,
    MessageType,
    SyncRequestPayload,
    SyncResponsePayload,
)
from swarm_orchestrator.gossip.transport import UDPTransport
from swarm_orchestrator.models import NodeState, NodeStatus, SwarmState

if TYPE_CHECKING:
    from swarm_orchestrator.config import SwarmConfig


class GossipProtocol:
    """Gossip protocol for state propagation and node discovery."""

    def __init__(
        self,
        node_state: NodeState,
        swarm_state: SwarmState,
        config: "SwarmConfig",
        transport: UDPTransport | None = None,
    ):
        self.node_state = node_state
        self.swarm_state = swarm_state
        self.config = config

        self.transport = transport or UDPTransport(
            bind_address=config.network.bind_address,
            gossip_port=config.network.gossip_port,
            multicast_group=config.network.multicast_group,
            multicast_port=config.network.multicast_port,
        )

        # Message deduplication cache (ordered for LRU behavior)
        self._seen_messages: OrderedDict[UUID, datetime] = OrderedDict()
        self._max_cache_size = config.gossip.message_cache_size

        # Protocol state
        self._running = False
        self._gossip_task: asyncio.Task[None] | None = None
        self._anti_entropy_task: asyncio.Task[None] | None = None

        # Callbacks
        self._on_node_discovered: list[callable] = []
        self._on_node_updated: list[callable] = []
        self._on_message_received: list[callable] = []

    def on_node_discovered(self, callback: callable) -> None:
        """Register callback for when a new node is discovered."""
        self._on_node_discovered.append(callback)

    def on_node_updated(self, callback: callable) -> None:
        """Register callback for when a node's state is updated."""
        self._on_node_updated.append(callback)

    def on_message_received(self, callback: callable) -> None:
        """Register callback for when any message is received."""
        self._on_message_received.append(callback)

    async def start(self) -> None:
        """Start the gossip protocol."""
        if self._running:
            return

        self.transport.set_message_handler(self._handle_message)
        await self.transport.start()
        self._running = True

        # Announce ourselves
        await self._send_announce()

        # Start background tasks
        loop = asyncio.get_event_loop()
        self._gossip_task = loop.create_task(self._gossip_loop())
        self._anti_entropy_task = loop.create_task(self._anti_entropy_loop())

    async def stop(self) -> None:
        """Stop the gossip protocol."""
        self._running = False

        # Send leave message
        await self._send_leave()

        if self._gossip_task:
            self._gossip_task.cancel()
            try:
                await self._gossip_task
            except asyncio.CancelledError:
                pass

        if self._anti_entropy_task:
            self._anti_entropy_task.cancel()
            try:
                await self._anti_entropy_task
            except asyncio.CancelledError:
                pass

        await self.transport.stop()

    async def _send_announce(self) -> None:
        """Announce this node to the swarm via multicast."""
        payload = AnnouncePayload(
            hostname=self.node_state.hostname,
            device_class=self.node_state.device_class.value,
            gossip_port=self.node_state.gossip_port,
        )

        message = GossipMessage(
            sender_id=self.node_state.node_id,
            sender_address=f"{self.node_state.ip_address}:{self.node_state.gossip_port}",
            message_type=MessageType.ANNOUNCE,
            payload=payload.model_dump(),
            term=self.swarm_state.current_term,
        )

        await self.transport.send_multicast(message)

    async def _send_leave(self) -> None:
        """Announce that this node is leaving."""
        message = GossipMessage(
            sender_id=self.node_state.node_id,
            sender_address=f"{self.node_state.ip_address}:{self.node_state.gossip_port}",
            message_type=MessageType.LEAVE,
            payload={},
            term=self.swarm_state.current_term,
        )

        await self.transport.send_multicast(message)

    async def _gossip_loop(self) -> None:
        """Main gossip loop - periodically propagate state."""
        interval = self.config.gossip.interval_ms / 1000.0

        while self._running:
            try:
                await asyncio.sleep(interval)
                await self._do_gossip_round()
            except asyncio.CancelledError:
                break
            except Exception:
                # Log and continue
                pass

    async def _do_gossip_round(self) -> None:
        """Perform one round of gossip."""
        # Select random nodes to gossip to
        other_nodes = [
            n for n in self.swarm_state.nodes.values()
            if n.node_id != self.node_state.node_id
        ]

        if not other_nodes:
            return

        # Select fanout number of nodes
        fanout = min(self.config.gossip.fanout, len(other_nodes))
        targets = random.sample(other_nodes, fanout)

        # Build gossip payload with current state
        payload = GossipPayload(
            nodes={
                str(n.node_id): n.model_dump(mode="json")
                for n in self.swarm_state.nodes.values()
            },
            leader_id=str(self.swarm_state.leader_id) if self.swarm_state.leader_id else None,
            term=self.swarm_state.current_term,
        )

        message = GossipMessage(
            sender_id=self.node_state.node_id,
            sender_address=f"{self.node_state.ip_address}:{self.node_state.gossip_port}",
            message_type=MessageType.GOSSIP,
            payload=payload.model_dump(),
            ttl=self.config.gossip.ttl,
            term=self.swarm_state.current_term,
        )

        # Send to each target
        for target in targets:
            try:
                await self.transport.send_unicast(
                    message, (target.ip_address, target.gossip_port)
                )
            except Exception:
                # Mark node as potentially unreachable
                pass

    async def _anti_entropy_loop(self) -> None:
        """Periodic full state sync."""
        interval = self.config.gossip.anti_entropy_interval_ms / 1000.0

        while self._running:
            try:
                await asyncio.sleep(interval)
                await self._do_anti_entropy()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _do_anti_entropy(self) -> None:
        """Perform anti-entropy sync with a random node."""
        other_nodes = [
            n for n in self.swarm_state.nodes.values()
            if n.node_id != self.node_state.node_id and n.is_alive()
        ]

        if not other_nodes:
            return

        target = random.choice(other_nodes)

        payload = SyncRequestPayload(
            known_nodes=list(self.swarm_state.nodes.keys()),
            term=self.swarm_state.current_term,
        )

        message = GossipMessage(
            sender_id=self.node_state.node_id,
            sender_address=f"{self.node_state.ip_address}:{self.node_state.gossip_port}",
            message_type=MessageType.SYNC_REQUEST,
            payload=payload.model_dump(),
            term=self.swarm_state.current_term,
        )

        await self.transport.send_unicast(message, (target.ip_address, target.gossip_port))

    async def _handle_message(
        self, message: GossipMessage, addr: tuple[str, int]
    ) -> None:
        """Handle an incoming message."""
        # Check for duplicates
        if message.message_id in self._seen_messages:
            return

        # Add to seen cache
        self._seen_messages[message.message_id] = datetime.now()
        self._prune_seen_cache()

        # Ignore our own messages
        if message.sender_id == self.node_state.node_id:
            return

        # Notify callbacks
        for callback in self._on_message_received:
            try:
                await callback(message, addr)
            except Exception:
                pass

        # Handle by type
        handlers = {
            MessageType.ANNOUNCE: self._handle_announce,
            MessageType.GOSSIP: self._handle_gossip,
            MessageType.LEAVE: self._handle_leave,
            MessageType.SYNC_REQUEST: self._handle_sync_request,
            MessageType.SYNC_RESPONSE: self._handle_sync_response,
        }

        handler = handlers.get(message.message_type)
        if handler:
            await handler(message, addr)

        # Forward if TTL allows
        if not message.is_expired() and message.message_type in (
            MessageType.ANNOUNCE,
            MessageType.LEAVE,
        ):
            await self._forward_message(message)

    async def _handle_announce(
        self, message: GossipMessage, addr: tuple[str, int]
    ) -> None:
        """Handle node announcement."""
        payload = AnnouncePayload(**message.payload)

        # Check if this is a new node
        is_new = str(message.sender_id) not in self.swarm_state.nodes

        # Create or update node state
        from swarm_orchestrator.models import DeviceClass, NodeRole

        node = NodeState(
            node_id=message.sender_id,
            hostname=payload.hostname,
            device_class=DeviceClass(payload.device_class),
            ip_address=addr[0],
            gossip_port=payload.gossip_port,
            role=NodeRole.FOLLOWER,
            last_seen=datetime.now(),
        )

        self.swarm_state.add_node(node)

        # Notify callbacks
        if is_new:
            for callback in self._on_node_discovered:
                try:
                    await callback(node)
                except Exception:
                    pass
        else:
            for callback in self._on_node_updated:
                try:
                    await callback(node)
                except Exception:
                    pass

    async def _handle_gossip(
        self, message: GossipMessage, addr: tuple[str, int]
    ) -> None:
        """Handle gossip state propagation."""
        payload = GossipPayload(**message.payload)

        # Merge node states
        for node_id_str, node_data in payload.nodes.items():
            # Skip our own state from others
            if node_id_str == str(self.node_state.node_id):
                continue

            existing = self.swarm_state.nodes.get(node_id_str)
            remote_last_seen = datetime.fromisoformat(node_data["last_seen"])

            # Accept if newer or unknown
            if not existing or remote_last_seen > existing.last_seen:
                node = NodeState(**node_data)
                is_new = existing is None
                self.swarm_state.add_node(node)

                if is_new:
                    for callback in self._on_node_discovered:
                        try:
                            await callback(node)
                        except Exception:
                            pass

        # Update term if higher
        if payload.term > self.swarm_state.current_term:
            self.swarm_state.current_term = payload.term

        # Update leader if term matches and we don't have one
        if payload.leader_id and payload.term >= self.swarm_state.current_term:
            leader_uuid = UUID(payload.leader_id)
            if self.swarm_state.leader_id != leader_uuid:
                self.swarm_state.set_leader(leader_uuid)

    async def _handle_leave(
        self, message: GossipMessage, addr: tuple[str, int]
    ) -> None:
        """Handle node leaving."""
        node = self.swarm_state.get_node(message.sender_id)
        if node:
            node.status = NodeStatus.UNREACHABLE
            self.swarm_state.remove_node(message.sender_id)

    async def _handle_sync_request(
        self, message: GossipMessage, addr: tuple[str, int]
    ) -> None:
        """Handle anti-entropy sync request."""
        payload = SyncResponsePayload(
            nodes={
                str(n.node_id): n.model_dump(mode="json")
                for n in self.swarm_state.nodes.values()
            },
            leader_id=str(self.swarm_state.leader_id) if self.swarm_state.leader_id else None,
            term=self.swarm_state.current_term,
        )

        response = GossipMessage(
            sender_id=self.node_state.node_id,
            sender_address=f"{self.node_state.ip_address}:{self.node_state.gossip_port}",
            message_type=MessageType.SYNC_RESPONSE,
            payload=payload.model_dump(),
            term=self.swarm_state.current_term,
        )

        # Parse sender address for reply
        sender_ip, sender_port = message.sender_address.rsplit(":", 1)
        await self.transport.send_unicast(response, (sender_ip, int(sender_port)))

    async def _handle_sync_response(
        self, message: GossipMessage, addr: tuple[str, int]
    ) -> None:
        """Handle anti-entropy sync response."""
        # Same as gossip handling
        await self._handle_gossip(message, addr)

    async def _forward_message(self, message: GossipMessage) -> None:
        """Forward a message to other nodes."""
        forwarded = message.decrement_ttl()
        if forwarded.is_expired():
            return

        # Select random nodes excluding sender
        other_nodes = [
            n for n in self.swarm_state.nodes.values()
            if n.node_id != self.node_state.node_id
            and n.node_id != message.sender_id
        ]

        if not other_nodes:
            return

        fanout = min(self.config.gossip.fanout, len(other_nodes))
        targets = random.sample(other_nodes, fanout)

        for target in targets:
            try:
                await self.transport.send_unicast(
                    forwarded, (target.ip_address, target.gossip_port)
                )
            except Exception:
                pass

    def _prune_seen_cache(self) -> None:
        """Remove old entries from seen message cache."""
        while len(self._seen_messages) > self._max_cache_size:
            self._seen_messages.popitem(last=False)

    async def broadcast_message(self, message: GossipMessage) -> None:
        """Broadcast a message to all known nodes."""
        for node in self.swarm_state.nodes.values():
            if node.node_id != self.node_state.node_id:
                try:
                    await self.transport.send_unicast(
                        message, (node.ip_address, node.gossip_port)
                    )
                except Exception:
                    pass
