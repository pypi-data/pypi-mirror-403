"""Green energy-focused dashboard for v0.2.0."""

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from swarm_orchestrator.core.node import Node
    from swarm_orchestrator.core.swarm import Swarm
    from swarm_orchestrator.gossip.adaptive import AdaptiveGossip, GossipMode
    from swarm_orchestrator.metrics.energy import EnergyCollector, EnergySample


# Energy efficiency rating thresholds
EFFICIENCY_RATINGS = [
    (90, "A+", "bright_green"),
    (80, "A", "green"),
    (70, "B", "yellow"),
    (60, "C", "orange1"),
    (50, "D", "red"),
    (0, "F", "bright_red"),
]

# Carbon intensity levels (gCO2/kWh)
CARBON_LEVELS = [
    (50, "Very Low", "bright_green"),
    (150, "Low", "green"),
    (300, "Medium", "yellow"),
    (500, "High", "orange1"),
    (float("inf"), "Very High", "red"),
]


def get_efficiency_rating(score: float) -> tuple[str, str]:
    """Get efficiency rating and color for a score."""
    for threshold, rating, color in EFFICIENCY_RATINGS:
        if score >= threshold:
            return rating, color
    return "F", "bright_red"


def get_carbon_level(intensity: float) -> tuple[str, str]:
    """Get carbon level description and color."""
    for threshold, level, color in CARBON_LEVELS:
        if intensity < threshold:
            return level, color
    return "Very High", "red"


def create_sparkline(values: list[float], width: int = 20) -> str:
    """Create a simple sparkline from values."""
    if not values:
        return " " * width

    # Sparkline characters (increasing height)
    chars = " ▁▂▃▄▅▆▇█"

    # Normalize values
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val if max_val != min_val else 1

    # Sample or pad to width
    if len(values) > width:
        # Sample evenly
        step = len(values) / width
        sampled = [values[int(i * step)] for i in range(width)]
    else:
        # Pad with zeros
        sampled = [0.0] * (width - len(values)) + values

    # Convert to sparkline
    result = ""
    for val in sampled:
        normalized = (val - min_val) / range_val
        idx = int(normalized * (len(chars) - 1))
        result += chars[idx]

    return result


class GreenDashboard:
    """Energy-focused terminal dashboard."""

    def __init__(
        self,
        node: "Node",
        energy_collector: "EnergyCollector | None" = None,
        adaptive_gossip: "AdaptiveGossip | None" = None,
    ):
        self.node = node
        self.energy_collector = energy_collector
        self.adaptive_gossip = adaptive_gossip
        self.swarm: "Swarm | None" = None
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
            Layout(name="right", size=45),
        )
        layout["left"].split_column(
            Layout(name="energy", size=12),
            Layout(name="nodes"),
        )
        layout["right"].split_column(
            Layout(name="efficiency", size=10),
            Layout(name="gossip", size=8),
            Layout(name="carbon"),
        )
        return layout

    def _render_header(self) -> Panel:
        """Render the header with energy-focused branding."""
        title = Text()
        title.append("🌱 ", style="green")
        title.append("SWARM ORCHESTRATOR", style="bold cyan")
        title.append(" GREEN EDITION", style="bold green")
        title.append(" | ", style="dim")
        title.append(f"Node: {self.node.name}", style="white")
        title.append(" | ", style="dim")

        if self.node.is_leader:
            title.append("⚡ LEADER", style="bold yellow")
        else:
            title.append("FOLLOWER", style="dim")

        return Panel(title, style="green")

    def _render_energy_panel(self) -> Panel:
        """Render the main energy metrics panel."""
        content = Table.grid(padding=(0, 2))
        content.add_column(style="cyan", justify="right", width=14)
        content.add_column(style="white", width=12)
        content.add_column(style="dim", width=20)

        if self.energy_collector:
            summary = self.energy_collector.get_summary()
            samples = self.energy_collector.get_recent_samples(20)
            power_values = [s.power_watts for s in samples]

            # Current power with sparkline
            content.add_row(
                "Power:",
                f"{summary['power_watts']:.2f} W",
                create_sparkline(power_values),
            )

            # Power state with indicator
            state = summary["power_state"]
            state_colors = {
                "active": "green",
                "idle": "blue",
                "low_power": "yellow",
                "critical": "red",
            }
            state_text = Text(state.upper(), style=state_colors.get(state, "white"))
            content.add_row("State:", state_text, "")

            # Temperature
            if summary["cpu_temp_c"]:
                temp = summary["cpu_temp_c"]
                temp_color = "green" if temp < 60 else "yellow" if temp < 75 else "red"
                content.add_row("CPU Temp:", Text(f"{temp:.1f}°C", style=temp_color), "")

            # Total energy
            content.add_row("Energy:", f"{summary['total_energy_wh']:.4f} Wh", "")
            content.add_row("", f"({summary['total_energy_j']:.1f} J)", "")

            # Peak/Avg power
            content.add_row("Avg Power:", f"{summary['avg_power_watts']:.2f} W", "")
            content.add_row("Peak:", f"{summary['peak_power_watts']:.2f} W", "")

        else:
            # Fallback to basic metrics
            metrics = self.node.state.metrics or {}
            content.add_row("Energy:", f"{metrics.get('total_energy_mj', 0):.1f} mJ", "")
            content.add_row("CPU:", f"{metrics.get('cpu_percent', 0):.1f}%", "")
            content.add_row("Memory:", f"{metrics.get('memory_mb', 0):.1f} MB", "")

        return Panel(content, title="⚡ Energy Metrics", border_style="yellow")

    def _render_efficiency_panel(self) -> Panel:
        """Render the efficiency rating panel."""
        content = Table.grid(padding=(0, 1))
        content.add_column(justify="center")

        if self.energy_collector:
            score = self.energy_collector.stats.efficiency_score
            rating, color = get_efficiency_rating(score)

            # Big rating display
            rating_text = Text()
            rating_text.append(f"\n  {rating}  \n", style=f"bold {color} on black")

            content.add_row(Panel(rating_text, style=color, padding=(0, 2)))
            content.add_row(Text(f"Score: {score:.1f}/100", style="white", justify="center"))

            # Efficiency bar
            progress = Progress(
                TextColumn("[cyan]Efficiency"),
                BarColumn(complete_style=color, finished_style=color),
                TextColumn(f"{score:.0f}%"),
                expand=True,
            )
            progress.add_task("", completed=score, total=100)
            content.add_row(progress)
        else:
            content.add_row(Text("N/A", style="dim", justify="center"))
            content.add_row(Text("Energy collector not available", style="dim"))

        return Panel(content, title="🏆 Efficiency Rating", border_style="green")

    def _render_gossip_panel(self) -> Panel:
        """Render the adaptive gossip panel."""
        content = Table.grid(padding=(0, 1))
        content.add_column(style="cyan", justify="right", width=12)
        content.add_column(style="white")

        if self.adaptive_gossip:
            summary = self.adaptive_gossip.get_summary()
            mode = summary["mode"]
            params = summary["params"]
            health = summary["network_health"]

            # Mode with color
            mode_colors = {
                "aggressive": "red",
                "normal": "green",
                "conservative": "blue",
                "emergency": "bright_red",
            }
            mode_text = Text(mode.upper(), style=f"bold {mode_colors.get(mode, 'white')}")
            content.add_row("Mode:", mode_text)

            content.add_row("Interval:", f"{params['interval_ms']} ms")
            content.add_row("Fanout:", str(params['fanout']))
            content.add_row("Health:", f"{health['score']:.0f}%")
        else:
            gossip_cfg = self.node.config.gossip
            content.add_row("Interval:", f"{gossip_cfg.interval_ms} ms")
            content.add_row("Fanout:", str(gossip_cfg.fanout))
            content.add_row("Mode:", Text("STATIC", style="dim"))

        return Panel(content, title="📡 Gossip", border_style="blue")

    def _render_carbon_panel(self) -> Panel:
        """Render the carbon footprint panel."""
        content = Table.grid(padding=(0, 1))
        content.add_column(style="cyan", justify="right", width=14)
        content.add_column(style="white")

        if self.energy_collector:
            summary = self.energy_collector.get_summary()
            carbon_g = summary["carbon_grams"]

            # Carbon footprint
            content.add_row("CO₂ Emitted:", f"{carbon_g:.4f} g")

            # Carbon intensity
            sample = self.energy_collector.get_latest_sample()
            if sample:
                intensity = sample.carbon_intensity_gco2_kwh
                level, color = get_carbon_level(intensity)
                content.add_row(
                    "Grid Carbon:",
                    Text(f"{intensity:.0f} gCO₂/kWh ({level})", style=color),
                )

            # Equivalent metrics
            content.add_row("", "")
            content.add_row("Equivalent:", "")

            # Trees needed to offset (1 tree absorbs ~21kg CO2/year)
            trees = carbon_g / (21000 / 365 / 24)  # Per hour
            content.add_row("  Trees/hr:", f"{trees:.6f}")

            # Phone charges (one charge ~8g CO2)
            charges = carbon_g / 8
            content.add_row("  Charges:", f"{charges:.4f}")

        else:
            content.add_row("CO₂:", Text("N/A", style="dim"))
            content.add_row("", Text("Requires energy collector", style="dim"))

        return Panel(content, title="🌍 Carbon Footprint", border_style="green")

    def _render_nodes_table(self) -> Panel:
        """Render the nodes table with energy info."""
        from swarm_orchestrator.core.swarm import Swarm

        if not self.swarm:
            self.swarm = Swarm(self.node)

        table = Table(show_header=True, header_style="bold magenta", expand=True)
        table.add_column("ID", style="dim", width=8)
        table.add_column("Host", style="cyan", width=12)
        table.add_column("Role", width=8)
        table.add_column("Status", width=8)
        table.add_column("Power", width=8, justify="right")
        table.add_column("Eff", width=5, justify="center")

        for node_data in self.swarm.get_node_table_data():
            role_style = "yellow bold" if node_data["role"] == "leader" else "dim"
            status_style = {
                "healthy": "green",
                "degraded": "yellow",
                "unreachable": "red",
            }.get(node_data["status"], "dim")

            hostname = node_data["hostname"][:10]
            if node_data["is_local"]:
                hostname = f"{hostname}*"

            # Get power/efficiency from node metrics if available
            power_str = "—"
            eff_str = "—"

            if node_data["is_local"] and self.energy_collector:
                summary = self.energy_collector.get_summary()
                power_str = f"{summary['power_watts']:.1f}W"
                rating, color = get_efficiency_rating(summary["efficiency_score"])
                eff_str = Text(rating, style=color)

            table.add_row(
                node_data["node_id"],
                hostname,
                Text(node_data["role"], style=role_style),
                Text(node_data["status"], style=status_style),
                power_str,
                eff_str,
            )

        return Panel(table, title="🖥️ Swarm Nodes", border_style="cyan")

    def _render_footer(self) -> Panel:
        """Render the footer."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        uptime = f"{self.node.uptime:.0f}s"

        footer = Text()
        footer.append("🌱 ", style="green")
        footer.append(f"Updated: {now}", style="dim")
        footer.append(" | ", style="dim")
        footer.append(f"Uptime: {uptime}", style="dim")
        footer.append(" | ", style="dim")

        # Show swarm totals
        if self.swarm:
            summary = self.swarm.get_status_summary()
            footer.append(f"Nodes: {summary['node_count']}", style="cyan")
            footer.append(" | ", style="dim")

        footer.append("Ctrl+C to exit", style="dim italic")

        return Panel(footer, style="green")

    def _render(self) -> Layout:
        """Render the complete green dashboard."""
        layout = self._create_layout()

        layout["header"].update(self._render_header())
        layout["energy"].update(self._render_energy_panel())
        layout["nodes"].update(self._render_nodes_table())
        layout["efficiency"].update(self._render_efficiency_panel())
        layout["gossip"].update(self._render_gossip_panel())
        layout["carbon"].update(self._render_carbon_panel())
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
        self.console.print(self._render_energy_panel())
        self.console.print(self._render_efficiency_panel())
        self.console.print(self._render_carbon_panel())
        self.console.print(self._render_nodes_table())
