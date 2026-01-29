"""Typer CLI for swarm orchestrator."""

import asyncio
import json
import signal
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from swarm_orchestrator.config import (
    DEFAULT_CONFIG_FILE,
    SwarmConfig,
    get_config_path,
    init_config,
    load_config,
)
from swarm_orchestrator.utils.display import (
    console,
    format_node_status,
    format_swarm_summary,
    format_swarm_table,
    print_error,
    print_info,
    print_success,
    print_warning,
)

app = typer.Typer(
    name="swarm",
    help="Swarm Orchestrator - AI agent swarms on edge/IoT hardware",
    no_args_is_help=True,
)

# Sub-commands
node_app = typer.Typer(help="Node management commands")
swarm_app = typer.Typer(help="Swarm operations")
config_app = typer.Typer(help="Configuration management")

app.add_typer(node_app, name="node")
app.add_typer(swarm_app, name="swarm")
app.add_typer(config_app, name="config")


# Global state for running node
_running_node = None


def _get_event_loop():
    """Get or create an event loop."""
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.new_event_loop()


# ============================================================================
# Node commands
# ============================================================================


@node_app.command("start")
def node_start(
    name: Annotated[Optional[str], typer.Option("--name", "-n", help="Node name")] = None,
    foreground: Annotated[bool, typer.Option("--foreground", "-f", help="Run in foreground")] = False,
    config_file: Annotated[Optional[Path], typer.Option("--config", "-c", help="Config file path")] = None,
):
    """Start a swarm node."""
    global _running_node

    try:
        config = load_config(config_file)
    except FileNotFoundError:
        print_warning("No config file found, using defaults")
        config = SwarmConfig()

    from swarm_orchestrator.core.node import Node

    node = Node(config=config, name=name)
    _running_node = node

    print_info(f"Starting node: {node.name}")
    print_info(f"Node ID: {node.node_id}")
    print_info(f"Address: {node.state.ip_address}:{node.state.gossip_port}")

    async def run_node():
        await node.start()
        print_success("Node started")

        # Set up signal handlers
        loop = asyncio.get_event_loop()

        def handle_signal():
            print_info("\nShutting down...")
            asyncio.create_task(shutdown())

        async def shutdown():
            await node.stop()
            print_success("Node stopped")
            loop.stop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, handle_signal)

        # Keep running
        if foreground:
            # Show live dashboard
            from swarm_orchestrator.metrics.dashboard import Dashboard

            dashboard = Dashboard(node)
            try:
                await dashboard.run()
            except asyncio.CancelledError:
                pass
        else:
            # Just wait
            while node.is_running:
                await asyncio.sleep(1)

    try:
        asyncio.run(run_node())
    except KeyboardInterrupt:
        pass


@node_app.command("stop")
def node_stop():
    """Stop the running node."""
    global _running_node

    if _running_node:
        asyncio.run(_running_node.stop())
        print_success("Node stopped")
    else:
        print_error("No node is running")


@node_app.command("status")
def node_status(
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
):
    """Show node status."""
    global _running_node

    if not _running_node:
        print_error("No node is running. Start one with: swarm node start")
        raise typer.Exit(1)

    if json_output:
        console.print_json(data=_running_node.get_status())
    else:
        console.print(format_node_status(_running_node.state, is_local=True))


# ============================================================================
# Swarm commands
# ============================================================================


@swarm_app.command("status")
def swarm_status(
    watch: Annotated[bool, typer.Option("--watch", "-w", help="Watch for changes")] = False,
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
):
    """Show swarm status."""
    global _running_node

    if not _running_node:
        print_error("No node is running. Start one with: swarm node start")
        raise typer.Exit(1)

    from swarm_orchestrator.core.swarm import Swarm

    swarm = Swarm(_running_node)

    if json_output:
        console.print_json(data=swarm.get_status_summary())
        return

    if watch:
        from swarm_orchestrator.metrics.dashboard import Dashboard

        dashboard = Dashboard(_running_node)
        asyncio.run(dashboard.run())
    else:
        console.print(format_swarm_summary(_running_node.swarm_state))
        console.print(format_swarm_table(
            _running_node.swarm_state,
            str(_running_node.node_id)
        ))


@swarm_app.command("dashboard")
def swarm_dashboard():
    """Show live dashboard."""
    global _running_node

    if not _running_node:
        print_error("No node is running. Start one with: swarm node start")
        raise typer.Exit(1)

    from swarm_orchestrator.metrics.dashboard import Dashboard

    dashboard = Dashboard(_running_node)
    try:
        asyncio.run(dashboard.run())
    except KeyboardInterrupt:
        pass


@swarm_app.command("green")
def swarm_green():
    """Show energy-focused green dashboard (v0.2.0)."""
    global _running_node

    if not _running_node:
        print_error("No node is running. Start one with: swarm node start")
        raise typer.Exit(1)

    from swarm_orchestrator.metrics.green_dashboard import GreenDashboard

    dashboard = GreenDashboard(
        node=_running_node,
        energy_collector=_running_node.energy_collector,
        adaptive_gossip=_running_node.adaptive_gossip,
    )
    try:
        asyncio.run(dashboard.run())
    except KeyboardInterrupt:
        pass


@swarm_app.command("energy")
def swarm_energy(
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
):
    """Show energy metrics (v0.2.0)."""
    global _running_node

    if not _running_node:
        print_error("No node is running. Start one with: swarm node start")
        raise typer.Exit(1)

    if not _running_node.energy_collector:
        print_warning("Energy collector not available")
        print_info("Ensure [energy] enabled = true in config")
        raise typer.Exit(1)

    energy = _running_node.energy_collector.get_summary()

    if json_output:
        console.print_json(data=energy)
    else:
        from rich.table import Table
        from rich.text import Text

        table = Table(title="Energy Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        # Current power
        table.add_row("Current Power", f"{energy['power_watts']:.2f} W")
        table.add_row("Power State", energy['power_state'].upper())

        if energy['cpu_temp_c']:
            table.add_row("CPU Temperature", f"{energy['cpu_temp_c']:.1f} C")

        table.add_row("", "")
        table.add_row("Total Energy", f"{energy['total_energy_wh']:.4f} Wh")
        table.add_row("", f"({energy['total_energy_j']:.1f} J)")

        table.add_row("", "")
        table.add_row("Avg Power", f"{energy['avg_power_watts']:.2f} W")
        table.add_row("Peak Power", f"{energy['peak_power_watts']:.2f} W")

        table.add_row("", "")
        table.add_row("Carbon Footprint", f"{energy['carbon_grams']:.4f} g CO2")

        # Efficiency with color
        score = energy['efficiency_score']
        if score >= 80:
            style = "green"
        elif score >= 60:
            style = "yellow"
        else:
            style = "red"
        table.add_row("Efficiency Score", Text(f"{score:.1f}/100", style=style))

        console.print(table)


@swarm_app.command("metrics")
def swarm_metrics(
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
):
    """Show swarm metrics."""
    global _running_node

    if not _running_node:
        print_error("No node is running. Start one with: swarm node start")
        raise typer.Exit(1)

    metrics = _running_node.state.metrics or {}

    if json_output:
        console.print_json(data=metrics)
    else:
        from rich.table import Table

        table = Table(title="Node Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        for key, value in metrics.items():
            if isinstance(value, float):
                table.add_row(key, f"{value:.2f}")
            else:
                table.add_row(key, str(value))

        console.print(table)


# ============================================================================
# Config commands
# ============================================================================


@config_app.command("init")
def config_init(
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite existing config")] = False,
):
    """Initialize configuration file."""
    try:
        path = init_config(force=force)
        print_success(f"Config file created: {path}")
    except FileExistsError as e:
        print_error(str(e))
        print_info("Use --force to overwrite")
        raise typer.Exit(1)


@config_app.command("show")
def config_show():
    """Show current configuration."""
    path = get_config_path()

    if not path.exists():
        print_warning("No config file found")
        print_info("Using default configuration")
        config = SwarmConfig()
    else:
        config = load_config()

    # Show as TOML
    import toml

    config_dict = config.model_dump(mode="json")
    if "node" in config_dict and "data_dir" in config_dict["node"]:
        config_dict["node"]["data_dir"] = str(config_dict["node"]["data_dir"])

    toml_str = toml.dumps(config_dict)
    syntax = Syntax(toml_str, "toml", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"Config: {path}", border_style="blue"))


@config_app.command("set")
def config_set(
    key: Annotated[str, typer.Argument(help="Config key (e.g., gossip.interval_ms)")],
    value: Annotated[str, typer.Argument(help="Value to set")],
):
    """Set a configuration value."""
    path = get_config_path()

    if not path.exists():
        print_warning("No config file found, creating with defaults")
        config = SwarmConfig()
    else:
        config = load_config()

    try:
        config.set_nested(key, value)
        config.save()
        print_success(f"Set {key} = {value}")
    except KeyError:
        print_error(f"Unknown config key: {key}")
        raise typer.Exit(1)
    except ValueError as e:
        print_error(f"Invalid value: {e}")
        raise typer.Exit(1)


@config_app.command("path")
def config_path():
    """Show config file path."""
    path = get_config_path()
    console.print(str(path))

    if path.exists():
        print_info("Config file exists")
    else:
        print_warning("Config file does not exist")


# ============================================================================
# Main
# ============================================================================


@app.callback()
def main():
    """Swarm Orchestrator - AI agent swarms on edge/IoT hardware."""
    pass


@app.command()
def version():
    """Show version information."""
    from swarm_orchestrator import __version__

    console.print(f"swarm-orchestrator {__version__}")


if __name__ == "__main__":
    app()
