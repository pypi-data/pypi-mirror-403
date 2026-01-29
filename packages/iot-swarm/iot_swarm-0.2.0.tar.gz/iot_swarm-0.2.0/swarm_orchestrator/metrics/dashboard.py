"""Rich terminal dashboard for swarm monitoring."""

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from swarm_orchestrator.core.node import Node
    from swarm_orchestrator.core.swarm import Swarm


class Dashboard:
    """Rich terminal dashboard for swarm status."""

    def __init__(self, node: "Node"):
        self.node = node
        self.swarm: "Swarm" = None  # Set when running
        self.console = Console()
        self._running = False

    def _create_layout(self) -> Layout:
        """Create the dashboard layout."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right", size=40),
        )
        return layout

    def _render_header(self) -> Panel:
        """Render the header panel."""
        title = Text()
        title.append("SWARM ORCHESTRATOR", style="bold cyan")
        title.append(" | ", style="dim")
        title.append(f"Node: {self.node.name}", style="green")
        title.append(" | ", style="dim")

        if self.node.is_leader:
            title.append("LEADER", style="bold yellow")
        else:
            title.append("FOLLOWER", style="dim")

        return Panel(title, style="blue")

    def _render_nodes_table(self) -> Panel:
        """Render the nodes table."""
        from swarm_orchestrator.core.swarm import Swarm

        if not self.swarm:
            self.swarm = Swarm(self.node)

        table = Table(show_header=True, header_style="bold magenta", expand=True)
        table.add_column("ID", style="dim", width=10)
        table.add_column("Hostname", style="cyan")
        table.add_column("Role", width=10)
        table.add_column("Status", width=12)
        table.add_column("Class", width=10)
        table.add_column("Address", style="dim")
        table.add_column("Last Seen", width=10)
        table.add_column("HB", width=6, justify="right")

        for node_data in self.swarm.get_node_table_data():
            role_style = "yellow bold" if node_data["role"] == "leader" else "dim"
            status_style = {
                "healthy": "green",
                "degraded": "yellow",
                "unreachable": "red",
            }.get(node_data["status"], "dim")

            hostname = node_data["hostname"]
            if node_data["is_local"]:
                hostname = f"{hostname} *"

            table.add_row(
                node_data["node_id"],
                hostname,
                Text(node_data["role"], style=role_style),
                Text(node_data["status"], style=status_style),
                node_data["device_class"],
                node_data["ip_address"],
                node_data["last_seen"],
                str(node_data["heartbeats"]),
            )

        return Panel(table, title="Swarm Nodes", border_style="green")

    def _render_metrics(self) -> Panel:
        """Render the metrics panel."""
        metrics = self.node.state.metrics or {}

        content = Table.grid(padding=(0, 1))
        content.add_column(style="cyan", justify="right")
        content.add_column(style="white")

        content.add_row("CPU:", f"{metrics.get('cpu_percent', 0):.1f}%")
        content.add_row("Memory:", f"{metrics.get('memory_mb', 0):.1f} MB")
        content.add_row("Mem %:", f"{metrics.get('memory_percent', 0):.1f}%")
        content.add_row("", "")
        content.add_row("Msgs Sent:", str(metrics.get("messages_sent", 0)))
        content.add_row("Msgs Recv:", str(metrics.get("messages_received", 0)))
        content.add_row("Gossip:", str(metrics.get("gossip_rounds", 0)))
        content.add_row("", "")
        content.add_row("Energy:", f"{metrics.get('total_energy_mj', 0):.1f} mJ")

        return Panel(content, title="Metrics", border_style="yellow")

    def _render_status(self) -> Panel:
        """Render the status panel."""
        from swarm_orchestrator.core.swarm import Swarm

        if not self.swarm:
            self.swarm = Swarm(self.node)

        summary = self.swarm.get_status_summary()

        content = Table.grid(padding=(0, 1))
        content.add_column(style="cyan", justify="right")
        content.add_column(style="white")

        content.add_row("Swarm:", summary["swarm_name"])
        content.add_row("Nodes:", str(summary["node_count"]))
        content.add_row("Healthy:", str(summary["healthy_count"]))
        content.add_row("Term:", str(summary["current_term"]))
        content.add_row("", "")

        leader_text = "This node" if summary["is_local_leader"] else (
            summary["leader_id"][:8] if summary["leader_id"] else "None"
        )
        content.add_row("Leader:", leader_text)

        return Panel(content, title="Swarm Status", border_style="blue")

    def _render_footer(self) -> Panel:
        """Render the footer panel."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        uptime = f"{self.node.uptime:.0f}s"

        footer = Text()
        footer.append(f"Updated: {now}", style="dim")
        footer.append(" | ", style="dim")
        footer.append(f"Uptime: {uptime}", style="dim")
        footer.append(" | ", style="dim")
        footer.append("Press Ctrl+C to exit", style="dim italic")

        return Panel(footer, style="dim")

    def _render(self) -> Layout:
        """Render the complete dashboard."""
        layout = self._create_layout()

        layout["header"].update(self._render_header())
        layout["left"].update(self._render_nodes_table())

        # Right side: stack status and metrics
        right_layout = Layout()
        right_layout.split_column(
            Layout(name="status"),
            Layout(name="metrics"),
        )
        right_layout["status"].update(self._render_status())
        right_layout["metrics"].update(self._render_metrics())
        layout["right"].update(right_layout)

        layout["footer"].update(self._render_footer())

        return layout

    async def run(self, refresh_rate: float = 1.0) -> None:
        """Run the dashboard with live updates."""
        from swarm_orchestrator.core.swarm import Swarm

        self.swarm = Swarm(self.node)
        self._running = True

        with Live(self._render(), refresh_per_second=1, console=self.console) as live:
            while self._running:
                try:
                    await asyncio.sleep(refresh_rate)
                    live.update(self._render())
                except asyncio.CancelledError:
                    break

    def stop(self) -> None:
        """Stop the dashboard."""
        self._running = False

    def print_status(self) -> None:
        """Print a one-time status view."""
        from swarm_orchestrator.core.swarm import Swarm

        self.swarm = Swarm(self.node)

        self.console.print(self._render_header())
        self.console.print(self._render_nodes_table())
        self.console.print(self._render_status())
        self.console.print(self._render_metrics())
