import asyncio
from pathlib import Path
from typing import Any

import httpx
import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from nopper.config import load_config, save_config, update_config
from nopper.node.config import NodeConfig
from nopper.node.manager import NodeManager, prompt_save_location

app = typer.Typer(help="Manage execution nodes (local, venv, machine, remote).")
console = Console()


@app.command("create")
def create_node(
    name: str = typer.Argument(..., help="Name of the node to create"),
    provider: str | None = typer.Option(None, "-p", "--provider", help="AI provider (e.g. openai, anthropic, ollama, openrouter)"),
    model: str | None = typer.Option(None, "-m", "--model", help="Default model name for this node"),
    url: str | None = typer.Option(None, "--url", help="Base URL for remote or local server"),
    key: str | None = typer.Option(None, "--key", help="API key for this node"),
    timeout: float | None = typer.Option(None, "--timeout", help="Timeout in seconds for this node (-1 for unlimited)"),
    location: str | None = typer.Option(None, "-l", "--location", help="Storage location: 'venv' or 'machine'"),
    path: str | None = typer.Option(None, "--path", help="Custom path when saving to machine (defaults to current working directory)"),
):
    """Create a new execution node with interactive storage location selection."""
    settings = load_config()

    # Resolve provider
    if not provider:
        provider = Prompt.ask(
            "Enter provider",
            default=settings.provider or "openai",
        )

    # Resolve model
    if not model:
        default_model = "llama3" if provider == "ollama" else ("gpt-4o" if provider == "openai" else settings.model)
        model = Prompt.ask("Enter model name", default=default_model)

    # Resolve key if needed and not provided
    if key is None and provider not in ["ollama", "local", "lm_studio", "vllm"] and not url:
        existing_key = settings.api_keys.get(provider)
        if not existing_key:
            prompt_key = Prompt.ask("Enter API key (press Enter to skip)", password=True, default="")
            key = prompt_key if prompt_key else None
        else:
            key = existing_key

    # Resolve storage location and path
    save_location = location
    save_path = path

    if not save_location and not save_path:
        loc_type, chosen_dir = prompt_save_location()
        save_location = loc_type
        save_path = str(chosen_dir)
    elif save_location == "machine" and not save_path:
        save_path = str(Path.cwd())

    config = NodeConfig(
        name=name,
        provider=provider,
        model=model,
        base_url=url,
        api_key=key,
        timeout=timeout if timeout is not None else float(settings.timeout),
    )

    saved_file = NodeManager.save(config, location=save_location, path=save_path)
    console.print(f"[green]Successfully created node:[/green] [bold]{name}[/bold]")
    console.print(f"[dim]Saved to:[/dim] [cyan]{saved_file}[/cyan]")


@app.command("add")
def add_node(
    name: str = typer.Argument(..., help="Name of the remote node"),
    url: str = typer.Option(..., "--url", help="Base URL for the node (e.g. http://100.x.y.z:11434/v1)"),
    key: str | None = typer.Option(None, "--key", help="Optional API key for the node"),
    model: str | None = typer.Option(None, "--model", help="Default model for this node"),
    timeout: float | None = typer.Option(None, "--timeout", help="Optional timeout in seconds for this node (-1 for unlimited)"),
    location: str | None = typer.Option(None, "-l", "--location", help="Storage location: 'venv' or 'machine'"),
    path: str | None = typer.Option(None, "--path", help="Custom path when saving to machine (defaults to current working directory)"),
):
    """Add a custom remote node to Nopper configuration."""
    save_location = location
    save_path = path

    if not save_location and not save_path:
        loc_type, chosen_dir = prompt_save_location()
        save_location = loc_type
        save_path = str(chosen_dir)
    elif save_location == "machine" and not save_path:
        save_path = str(Path.cwd())

    config = NodeConfig(
        name=name,
        provider="remote" if "http" in url else "openai",
        base_url=url,
        api_key=key,
        model=model,
        timeout=timeout,
    )

    saved_file = NodeManager.save(config, location=save_location, path=save_path)
    console.print(f"[green]Successfully added remote node:[/green] [bold]{name}[/bold]")
    console.print(f"[dim]Saved to:[/dim] [cyan]{saved_file}[/cyan]")


@app.command("list")
def list_nodes():
    """List all registered execution nodes and their save locations."""
    details = NodeManager.list_detailed()

    if not details:
        console.print("[yellow]No nodes configured.[/yellow]")
        return

    async def check_node(item: dict[str, Any]):
        base_url = item.get("base_url")
        if not base_url:
            return item["name"], "[cyan]Standard[/cyan]", None
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                headers = {}
                # If key exists
                res = await client.get(f"{base_url}/models", headers=headers)
                if res.status_code == 200:
                    return item["name"], "[green]ONLINE[/green]", res.elapsed.total_seconds()
                return item["name"], f"[yellow]HTTP {res.status_code}[/yellow]", None
        except Exception:
            return item["name"], "[red]OFFLINE[/red]", None

    async def run_checks():
        tasks = [check_node(d) for d in details]
        return await asyncio.gather(*tasks)

    with console.status("[blue]Checking nodes...[/blue]"):
        results = asyncio.run(run_checks())

    results_dict = {name: (status, latency) for name, status, latency in results}

    table = Table(title="Execution Nodes")
    table.add_column("Name", style="cyan")
    table.add_column("Provider", style="blue")
    table.add_column("Model", style="green")
    table.add_column("Location", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Path", style="dim")

    for item in details:
        name = item["name"]
        status, latency = results_dict.get(name, ("[red]UNKNOWN[/red]", None))
        status_str = f"{status} ({latency:.2f}s)" if latency is not None else status
        table.add_row(
            name,
            item["provider"],
            item["model"] or "default",
            item["location_type"],
            status_str,
            item["path"],
        )

    console.print(table)


@app.command("show")
def show_node(name: str = typer.Argument(..., help="Name of the node to view")):
    """Show details and file path for a node."""
    path = NodeManager.find_node_path(name)
    try:
        config = NodeManager.get_config(name)
        console.print(f"[bold cyan]Node:[/bold cyan] {name}")
        console.print(f"[bold cyan]Path:[/bold cyan] {path or 'In memory/legacy'}")
        console.print(config.model_dump_json(indent=2))
    except Exception as e:
        console.print(f"[red]Error loading node '{name}':[/red] {e}")
        raise typer.Exit(1)


@app.command("remove")
def remove_node(name: str = typer.Argument(..., help="Name of the node to remove")):
    """Remove a registered node from storage."""
    deleted = NodeManager.delete(name)
    if deleted:
        console.print(f"[green]Successfully removed node:[/green] [bold]{name}[/bold]")
    else:
        # Check legacy config
        config = load_config()
        if name in config.nodes:
            del config.nodes[name]
            save_config(config)
            console.print(f"[green]Successfully removed node:[/green] [bold]{name}[/bold]")
        else:
            console.print(f"[red]Error:[/red] Node '{name}' not found.")
            raise typer.Exit(1)


@app.command("use")
def use_node(name: str = typer.Argument(..., help="Name of the node to use")):
    """Switch the globally active provider/node."""
    all_nodes = NodeManager.list()
    config = load_config()

    if name not in all_nodes and name not in config.nodes:
        console.print(f"[red]Error:[/red] Node '{name}' not found. Available nodes: {', '.join(all_nodes)}")
        raise typer.Exit(1)

    try:
        update_config("default_node", name)
        update_config("provider", name)
        console.print(f"[green]Successfully switched to node:[/green] [bold]{name}[/bold]")
    except Exception as e:
        console.print(f"[red]Failed to update configuration:[/red] {e}")
        raise typer.Exit(1)


@app.command("update")
def update_node(
    name: str = typer.Argument(..., help="Name of the node to update"),
    provider: str | None = typer.Option(None, "-c", "--provider", help="Update provider for this node"),
    url: str | None = typer.Option(None, "--url", help="Update Base URL"),
    key: str | None = typer.Option(None, "--key", help="Update API key"),
    model: str | None = typer.Option(None, "--model", help="Update model"),
    timeout: float | None = typer.Option(None, "--timeout", help="Update timeout in seconds (-1 for unlimited)"),
):
    """Update an existing node."""
    try:
        node_cfg = NodeManager.get_config(name)
    except Exception:
        node_cfg = None

    if node_cfg is None:
        console.print(f"[red]Error:[/red] Node '{name}' not found.")
        raise typer.Exit(1)

    if provider:
        node_cfg.provider = provider
    if url:
        node_cfg.base_url = url
    if key:
        node_cfg.api_key = key
    if model:
        node_cfg.model = model
    if timeout is not None:
        node_cfg.timeout = timeout

    path = NodeManager.find_node_path(name)
    saved_path = NodeManager.save(node_cfg, path=path)
    console.print(f"[green]Successfully updated node:[/green] [bold]{name}[/bold] ([dim]{saved_path}[/dim])")
