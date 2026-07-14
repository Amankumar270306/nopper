import asyncio

import httpx
import typer
from rich.console import Console
from rich.table import Table

from nopper.config import NodeConfig, load_config, save_config, update_config

app = typer.Typer()
console = Console()

@app.command("add")
def add_node(
    name: str = typer.Argument(..., help="Name of the remote node"),
    url: str = typer.Option(..., "--url", help="Base URL for the node (e.g. http://100.x.y.z:11434/v1)"),
    key: str | None = typer.Option(None, "--key", help="Optional API key for the node"),
    model: str | None = typer.Option(None, "--model", help="Default model for this node"),
    timeout: float | None = typer.Option(None, "--timeout", help="Optional timeout in seconds for this node")
):
    """Add a custom remote node to Nopper configuration."""
    config = load_config()
    
    if name in config.nodes:
        console.print(f"[yellow]Node '{name}' already exists. Overwriting.[/yellow]")
        
    config.nodes[name] = NodeConfig(
        base_url=url,
        api_key=key,
        model=model,
        timeout=timeout
    )
    
    save_config(config)
    console.print(f"[green]Successfully added remote node:[/green] [bold]{name}[/bold]")

@app.command("list")
def list_nodes():
    """List all registered remote nodes."""
    config = load_config()
    
    if not config.nodes:
        console.print("[yellow]No remote nodes configured.[/yellow]")
        return
        
    async def check_node(name: str, node: NodeConfig):
        if not node.base_url:
            return name, "[cyan]N/A (Standard)[/cyan]", None
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                headers = {}
                if node.api_key:
                    headers["Authorization"] = f"Bearer {node.api_key}"
                response = await client.get(f"{node.base_url}/models", headers=headers)
                
                if response.status_code == 200:
                    return name, "[green]ONLINE[/green]", response.elapsed.total_seconds()
                else:
                    return name, f"[yellow]HTTP {response.status_code}[/yellow]", None
        except Exception:
            return name, "[red]OFFLINE[/red]", None

    async def run_checks():
        tasks = [check_node(name, node) for name, node in config.nodes.items()]
        return await asyncio.gather(*tasks)

    with console.status("[blue]Pinging nodes...[/blue]"):
        results = asyncio.run(run_checks())

    table = Table(title="Remote Nodes")
    table.add_column("Name", style="cyan")
    table.add_column("Base URL", style="blue")
    table.add_column("Status", justify="center")
    table.add_column("Latency", justify="right")
    table.add_column("Model")
    
    
    results_dict = {name: (status, latency) for name, status, latency in results}
    
    for name, node in config.nodes.items():
        status, latency = results_dict.get(name, ("[red]UNKNOWN[/red]", None))
        lat_str = f"{latency:.2f}s" if latency is not None else "-"
        table.add_row(
            name, 
            node.base_url or f"Standard ({node.type})", 
            status, 
            lat_str, 
            node.model or "Not Set"
        )
        
    console.print(table)

@app.command("remove")
def remove_node(name: str = typer.Argument(..., help="Name of the node to remove")):
    """Remove a registered node from config."""
    config = load_config()
    
    if name not in config.nodes:
        console.print(f"[red]Error:[/red] Node '{name}' not found.")
        raise typer.Exit(1)
        
    del config.nodes[name]
    save_config(config)
    console.print(f"[green]Successfully removed node:[/green] [bold]{name}[/bold]")

@app.command("use")
def use_node(name: str = typer.Argument(..., help="Name of the node to use")):
    """Switch the globally active provider to the specified remote node."""
    config = load_config()
    
    if name not in config.nodes:
        console.print(f"[red]Error:[/red] Node '{name}' not found.")
        raise typer.Exit(1)
        
    try:
        update_config("provider", name)
        console.print(f"[green]Successfully switched to node:[/green] [bold]{name}[/bold]")
    except Exception as e:
        console.print(f"[red]Failed to update configuration:[/red] {e}")
        raise typer.Exit(1)

@app.command("update")
def update_node(
    name: str = typer.Argument(..., help="Name of the node to update"),
    provider: str | None = typer.Option(None, "-c", "--provider", help="Update internal provider for this node"),
    url: str | None = typer.Option(None, "--url", help="Update Base URL"),
    key: str | None = typer.Option(None, "--key", help="Update API key"),
    model: str | None = typer.Option(None, "--model", help="Update model")
):
    """Update an existing node."""
    config = load_config()
    if name not in config.nodes:
        console.print(f"[red]Error:[/red] Node '{name}' not found.")
        raise typer.Exit(1)
        
    node = config.nodes[name]
    if provider:
        node.type = provider
    if url:
        node.base_url = url
    if key:
        node.api_key = key
    if model:
        node.model = model
        
    save_config(config)
    console.print(f"[green]Successfully updated node:[/green] [bold]{name}[/bold]")
