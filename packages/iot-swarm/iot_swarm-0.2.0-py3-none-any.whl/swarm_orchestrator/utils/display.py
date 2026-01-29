"""Rich formatting utilities."""

from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from swarm_orchestrator.models import NodeState, SwarmState

# Global console instance
console = Console()


def format_node_status(node: "NodeState", is_local: bool = False) -> Panel:
    """Format a node's status as a Rich panel."""
    content = Table.grid(padding=(0, 1))
    content.add_column(style="cyan", justify="right")
    content.add_column(style="white")

    content.add_row("Node ID:", str(node.node_id)[:8] + "...")
    content.add_row("Hostname:", node.hostname + (" (local)" if is_local else ""))
    content.add_row("Role:", _style_role(node.role.value))
    content.add_row("Status:", _style_status(node.status.value))
    content.add_row("Device Class:", node.device_class.value)
    content.add_row("Address:", f"{node.ip_address}:{node.gossip_port}")
    content.add_row("Heartbeats:", str(node.heartbeat_count))
    content.add_row("Last Seen:", node.last_seen.strftime("%H:%M:%S"))

    if node.metrics:
        content.add_row("", "")
        content.add_row("CPU:", f"{node.metrics.get('cpu_percent', 0):.1f}%")
        content.add_row("Memory:", f"{node.metrics.get('memory_mb', 0):.1f} MB")

    title = "Node Status"
    if is_local:
        title = "Local Node Status"

    return Panel(content, title=title, border_style="green")


def format_swarm_table(swarm_state: "SwarmState", local_node_id: str | None = None) -> Table:
    """Format swarm state as a Rich table."""
    table = Table(
        show_header=True,
        header_style="bold magenta",
        title="Swarm Nodes",
        expand=True,
    )

    table.add_column("ID", style="dim", width=10)
    table.add_column("Hostname", style="cyan")
    table.add_column("Role", width=10)
    table.add_column("Status", width=12)
    table.add_column("Class", width=10)
    table.add_column("Address", style="dim")
    table.add_column("Last Seen", width=10)
    table.add_column("HB", width=6, justify="right")

    # Sort nodes: leader first, then by hostname
    nodes = sorted(
        swarm_state.nodes.values(),
        key=lambda n: (n.role.value != "leader", n.hostname),
    )

    for node in nodes:
        is_local = str(node.node_id) == local_node_id
        hostname = node.hostname + (" *" if is_local else "")

        table.add_row(
            str(node.node_id)[:8],
            hostname,
            _style_role(node.role.value),
            _style_status(node.status.value),
            node.device_class.value,
            f"{node.ip_address}:{node.gossip_port}",
            node.last_seen.strftime("%H:%M:%S"),
            str(node.heartbeat_count),
        )

    return table


def format_swarm_summary(swarm_state: "SwarmState") -> Panel:
    """Format swarm summary as a Rich panel."""
    content = Table.grid(padding=(0, 1))
    content.add_column(style="cyan", justify="right")
    content.add_column(style="white")

    content.add_row("Swarm ID:", str(swarm_state.swarm_id)[:8] + "...")
    content.add_row("Name:", swarm_state.swarm_name)
    content.add_row("Nodes:", str(swarm_state.node_count))
    content.add_row("Healthy:", str(swarm_state.healthy_count))
    content.add_row("Term:", str(swarm_state.current_term))

    if swarm_state.leader_id:
        leader = swarm_state.get_leader()
        leader_info = leader.hostname if leader else str(swarm_state.leader_id)[:8]
        content.add_row("Leader:", leader_info)
    else:
        content.add_row("Leader:", Text("None", style="yellow"))

    return Panel(content, title="Swarm Summary", border_style="blue")


def _style_role(role: str) -> Text:
    """Style a role value."""
    styles = {
        "leader": "yellow bold",
        "follower": "dim",
        "candidate": "cyan",
    }
    return Text(role, style=styles.get(role, "white"))


def _style_status(status: str) -> Text:
    """Style a status value."""
    styles = {
        "healthy": "green",
        "degraded": "yellow",
        "unreachable": "red",
    }
    return Text(status, style=styles.get(status, "white"))


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]![/yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]i[/blue] {message}")
