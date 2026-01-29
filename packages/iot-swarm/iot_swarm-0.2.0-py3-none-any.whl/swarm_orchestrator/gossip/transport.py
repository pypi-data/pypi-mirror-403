"""UDP transport for gossip protocol."""

import asyncio
import socket
import struct
from collections.abc import Callable
from typing import Any

from swarm_orchestrator.gossip.message import GossipMessage


class UDPTransport:
    """UDP transport layer for gossip messages."""

    def __init__(
        self,
        bind_address: str = "0.0.0.0",
        gossip_port: int = 5555,
        multicast_group: str = "239.255.255.250",
        multicast_port: int = 5556,
    ):
        self.bind_address = bind_address
        self.gossip_port = gossip_port
        self.multicast_group = multicast_group
        self.multicast_port = multicast_port

        self._unicast_socket: socket.socket | None = None
        self._multicast_socket: socket.socket | None = None
        self._running = False
        self._message_handler: Callable[[GossipMessage, tuple[str, int]], Any] | None = None
        self._receive_task: asyncio.Task[None] | None = None
        self._multicast_task: asyncio.Task[None] | None = None

    def set_message_handler(
        self, handler: Callable[[GossipMessage, tuple[str, int]], Any]
    ) -> None:
        """Set the callback for received messages."""
        self._message_handler = handler

    async def start(self) -> None:
        """Start the transport layer."""
        if self._running:
            return

        # Create unicast socket for direct communication
        self._unicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._unicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._unicast_socket.setblocking(False)
        self._unicast_socket.bind((self.bind_address, self.gossip_port))

        # Create multicast socket for discovery
        self._multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._multicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        self._multicast_socket.setblocking(False)

        # Join multicast group
        try:
            self._multicast_socket.bind(("", self.multicast_port))
            mreq = struct.pack(
                "4sl", socket.inet_aton(self.multicast_group), socket.INADDR_ANY
            )
            self._multicast_socket.setsockopt(
                socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq
            )
        except OSError:
            # Multicast might not be available (e.g., in containers)
            pass

        self._running = True

        # Start receive loops
        loop = asyncio.get_event_loop()
        self._receive_task = loop.create_task(self._receive_loop())
        self._multicast_task = loop.create_task(self._multicast_receive_loop())

    async def stop(self) -> None:
        """Stop the transport layer."""
        self._running = False

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self._multicast_task:
            self._multicast_task.cancel()
            try:
                await self._multicast_task
            except asyncio.CancelledError:
                pass

        if self._unicast_socket:
            self._unicast_socket.close()
            self._unicast_socket = None

        if self._multicast_socket:
            # Leave multicast group
            try:
                mreq = struct.pack(
                    "4sl", socket.inet_aton(self.multicast_group), socket.INADDR_ANY
                )
                self._multicast_socket.setsockopt(
                    socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq
                )
            except OSError:
                pass
            self._multicast_socket.close()
            self._multicast_socket = None

    async def send_unicast(self, message: GossipMessage, address: tuple[str, int]) -> None:
        """Send a message to a specific node."""
        if not self._unicast_socket:
            raise RuntimeError("Transport not started")

        data = message.to_bytes()
        loop = asyncio.get_event_loop()
        await loop.sock_sendto(self._unicast_socket, data, address)

    async def send_multicast(self, message: GossipMessage) -> None:
        """Send a message to the multicast group."""
        if not self._unicast_socket:
            raise RuntimeError("Transport not started")

        data = message.to_bytes()
        # Use unicast socket to send to multicast address
        loop = asyncio.get_event_loop()
        await loop.sock_sendto(
            self._unicast_socket, data, (self.multicast_group, self.multicast_port)
        )

    async def _receive_loop(self) -> None:
        """Receive loop for unicast messages."""
        if not self._unicast_socket:
            return

        loop = asyncio.get_event_loop()
        while self._running:
            try:
                data, addr = await loop.sock_recvfrom(self._unicast_socket, 65535)
                await self._handle_received(data, addr)
            except asyncio.CancelledError:
                break
            except Exception:
                if self._running:
                    await asyncio.sleep(0.1)

    async def _multicast_receive_loop(self) -> None:
        """Receive loop for multicast messages."""
        if not self._multicast_socket:
            return

        loop = asyncio.get_event_loop()
        while self._running:
            try:
                data, addr = await loop.sock_recvfrom(self._multicast_socket, 65535)
                await self._handle_received(data, addr)
            except asyncio.CancelledError:
                break
            except Exception:
                if self._running:
                    await asyncio.sleep(0.1)

    async def _handle_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle a received message."""
        if not self._message_handler:
            return

        try:
            message = GossipMessage.from_bytes(data)
            await self._message_handler(message, addr)
        except Exception:
            # Invalid message, ignore
            pass

    def get_local_address(self) -> tuple[str, int]:
        """Get the local address this transport is bound to."""
        if self._unicast_socket:
            return self._unicast_socket.getsockname()
        return (self.bind_address, self.gossip_port)

    @property
    def is_running(self) -> bool:
        """Check if transport is running."""
        return self._running
