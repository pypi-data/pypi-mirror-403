"""Leader election using Raft-inspired protocol."""

import asyncio
import random
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from swarm_orchestrator.gossip.message import (
    GossipMessage,
    HeartbeatPayload,
    MessageType,
    VoteRequestPayload,
    VoteResponsePayload,
)
from swarm_orchestrator.models import NodeRole, NodeState, SwarmState

if TYPE_CHECKING:
    from swarm_orchestrator.config import SwarmConfig
    from swarm_orchestrator.gossip.protocol import GossipProtocol


class LeaderElection:
    """Raft-inspired leader election."""

    def __init__(
        self,
        node_state: NodeState,
        swarm_state: SwarmState,
        config: "SwarmConfig",
        gossip: "GossipProtocol",
    ):
        self.node_state = node_state
        self.swarm_state = swarm_state
        self.config = config
        self.gossip = gossip

        # Election state
        self._last_heartbeat = datetime.now()
        self._votes_received: set[UUID] = set()
        self._election_in_progress = False

        # Tasks
        self._running = False
        self._heartbeat_task: asyncio.Task | None = None
        self._election_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start leader election protocol."""
        if self._running:
            return

        self._running = True

        # Register message handlers
        self.gossip.on_message_received(self._handle_message)

        # Start election timer
        loop = asyncio.get_event_loop()
        self._election_task = loop.create_task(self._election_timer_loop())

        # If we can be leader, start heartbeat loop (will only send if we are leader)
        if self.node_state.can_be_leader():
            self._heartbeat_task = loop.create_task(self._heartbeat_loop())

    async def stop(self) -> None:
        """Stop leader election protocol."""
        self._running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        if self._election_task:
            self._election_task.cancel()
            try:
                await self._election_task
            except asyncio.CancelledError:
                pass

    async def _heartbeat_loop(self) -> None:
        """Send heartbeats if we are the leader."""
        interval = self.config.consensus.heartbeat_interval_ms / 1000.0

        while self._running:
            try:
                await asyncio.sleep(interval)
                if self.node_state.role == NodeRole.LEADER:
                    await self._send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _send_heartbeat(self) -> None:
        """Send heartbeat to all followers."""
        self.node_state.increment_heartbeat()

        payload = HeartbeatPayload(
            leader_id=self.node_state.node_id,
            term=self.swarm_state.current_term,
            heartbeat_count=self.node_state.heartbeat_count,
            node_count=self.swarm_state.node_count,
        )

        message = GossipMessage(
            sender_id=self.node_state.node_id,
            sender_address=f"{self.node_state.ip_address}:{self.node_state.gossip_port}",
            message_type=MessageType.HEARTBEAT,
            payload=payload.model_dump(),
            term=self.swarm_state.current_term,
            ttl=1,  # Heartbeats don't need to propagate
        )

        await self.gossip.broadcast_message(message)

    async def _election_timer_loop(self) -> None:
        """Check for election timeout and start elections."""
        while self._running:
            try:
                # Randomize timeout to prevent split votes
                timeout = random.uniform(
                    self.config.consensus.election_timeout_min_ms / 1000.0,
                    self.config.consensus.election_timeout_max_ms / 1000.0,
                )
                await asyncio.sleep(timeout)
                await self.check_election()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def check_election(self) -> None:
        """Check if we should start an election."""
        # Don't start election if we're the leader
        if self.node_state.role == NodeRole.LEADER:
            return

        # Don't start if we can't be leader
        if not self.node_state.can_be_leader():
            return

        # Don't start if election already in progress
        if self._election_in_progress:
            return

        # Check if we've heard from leader recently
        timeout = self.config.consensus.election_timeout_max_ms / 1000.0
        time_since_heartbeat = (datetime.now() - self._last_heartbeat).total_seconds()

        if time_since_heartbeat > timeout:
            await self._start_election()

    async def _start_election(self) -> None:
        """Start a new election."""
        self._election_in_progress = True
        self._votes_received.clear()

        # Increment term and become candidate
        self.swarm_state.current_term += 1
        self.node_state.term = self.swarm_state.current_term
        self.node_state.role = NodeRole.CANDIDATE
        self.node_state.voted_for = self.node_state.node_id

        # Vote for ourselves
        self._votes_received.add(self.node_state.node_id)

        # Request votes from others
        payload = VoteRequestPayload(
            candidate_id=self.node_state.node_id,
            term=self.swarm_state.current_term,
            last_heartbeat_count=self.node_state.heartbeat_count,
        )

        message = GossipMessage(
            sender_id=self.node_state.node_id,
            sender_address=f"{self.node_state.ip_address}:{self.node_state.gossip_port}",
            message_type=MessageType.VOTE_REQUEST,
            payload=payload.model_dump(),
            term=self.swarm_state.current_term,
            ttl=1,
        )

        await self.gossip.broadcast_message(message)

        # Wait for votes
        await asyncio.sleep(self.config.consensus.vote_timeout_ms / 1000.0)

        # Check if we won
        await self._tally_votes()

        self._election_in_progress = False

    async def _tally_votes(self) -> None:
        """Check if we have enough votes to become leader."""
        if self.node_state.role != NodeRole.CANDIDATE:
            return

        eligible_voters = len(self.swarm_state.get_eligible_leaders())
        votes_needed = (eligible_voters // 2) + 1

        if len(self._votes_received) >= votes_needed:
            # We won!
            self.node_state.role = NodeRole.LEADER
            self.swarm_state.set_leader(self.node_state.node_id)
            self._last_heartbeat = datetime.now()

            # Send immediate heartbeat to establish leadership
            await self._send_heartbeat()
        else:
            # Election failed, revert to follower
            self.node_state.role = NodeRole.FOLLOWER
            self.node_state.voted_for = None

    async def _handle_message(
        self, message: GossipMessage, addr: tuple[str, int]
    ) -> None:
        """Handle election-related messages."""
        if message.message_type == MessageType.HEARTBEAT:
            await self._handle_heartbeat(message)
        elif message.message_type == MessageType.VOTE_REQUEST:
            await self._handle_vote_request(message)
        elif message.message_type == MessageType.VOTE_RESPONSE:
            await self._handle_vote_response(message)

    async def _handle_heartbeat(self, message: GossipMessage) -> None:
        """Handle heartbeat from leader."""
        payload = HeartbeatPayload(**message.payload)

        # Update term if higher
        if payload.term > self.swarm_state.current_term:
            self.swarm_state.current_term = payload.term
            self.node_state.term = payload.term
            self.node_state.voted_for = None

            # Step down if we were candidate/leader
            if self.node_state.role in (NodeRole.CANDIDATE, NodeRole.LEADER):
                self.node_state.role = NodeRole.FOLLOWER

        # Accept heartbeat if term matches or is higher
        if payload.term >= self.swarm_state.current_term:
            self._last_heartbeat = datetime.now()
            self.swarm_state.set_leader(payload.leader_id)

            # Update leader's heartbeat count
            leader = self.swarm_state.get_node(payload.leader_id)
            if leader:
                leader.heartbeat_count = payload.heartbeat_count
                leader.touch()

            # Ensure we're a follower
            if self.node_state.role != NodeRole.LEADER:
                self.node_state.role = NodeRole.FOLLOWER

    async def _handle_vote_request(self, message: GossipMessage) -> None:
        """Handle vote request from candidate."""
        payload = VoteRequestPayload(**message.payload)

        vote_granted = False
        reason = ""

        # Check term
        if payload.term < self.swarm_state.current_term:
            reason = "stale term"
        elif payload.term > self.swarm_state.current_term:
            # Update to new term
            self.swarm_state.current_term = payload.term
            self.node_state.term = payload.term
            self.node_state.voted_for = None
            self.node_state.role = NodeRole.FOLLOWER

        # Check if we've already voted in this term
        if not reason:
            if self.node_state.voted_for is None:
                # Grant vote
                self.node_state.voted_for = payload.candidate_id
                vote_granted = True
            elif self.node_state.voted_for == payload.candidate_id:
                # Already voted for this candidate
                vote_granted = True
            else:
                reason = "already voted"

        # Send response
        response_payload = VoteResponsePayload(
            voter_id=self.node_state.node_id,
            term=self.swarm_state.current_term,
            vote_granted=vote_granted,
            reason=reason,
        )

        response = GossipMessage(
            sender_id=self.node_state.node_id,
            sender_address=f"{self.node_state.ip_address}:{self.node_state.gossip_port}",
            message_type=MessageType.VOTE_RESPONSE,
            payload=response_payload.model_dump(),
            term=self.swarm_state.current_term,
            ttl=1,
        )

        # Send to candidate
        sender_ip, sender_port = message.sender_address.rsplit(":", 1)
        await self.gossip.transport.send_unicast(response, (sender_ip, int(sender_port)))

    async def _handle_vote_response(self, message: GossipMessage) -> None:
        """Handle vote response."""
        if self.node_state.role != NodeRole.CANDIDATE:
            return

        payload = VoteResponsePayload(**message.payload)

        # Check term
        if payload.term > self.swarm_state.current_term:
            # Step down
            self.swarm_state.current_term = payload.term
            self.node_state.term = payload.term
            self.node_state.role = NodeRole.FOLLOWER
            self.node_state.voted_for = None
            return

        if payload.vote_granted and payload.term == self.swarm_state.current_term:
            self._votes_received.add(payload.voter_id)
