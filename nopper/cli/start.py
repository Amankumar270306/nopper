import typer
from rich.console import Console
from rich.prompt import IntPrompt, Prompt

from nopper import AI
from nopper.config import load_config, update_config

app = typer.Typer(help="Interactive setup wizard for Nopper.")
console = Console()

PROVIDER_MAP = {
    1: "openai",
    2: "openrouter",
    3: "ollama",
    4: "anthropic",
    5: "gemini",
    6: "groq",
    7: "together",
    8: "mistral",
    9: "local",
    10: "lm_studio",
    11: "vllm",
    12: "custom_node"
}

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is not None:
        return

    console.print("\n[bold cyan]Welcome to the Nopper Setup Wizard![/bold cyan]\n")
    console.print("Select your AI provider:")

    for num, name in PROVIDER_MAP.items():

        display_name = name
        if name == "local": display_name = "Local OpenAI-compatible servers"
        if name == "lm_studio": display_name = "LM Studio"
        if name == "vllm": display_name = "vLLM"
        if name == "anthropic": display_name = "Claude"
        if name == "gemini": display_name = "Gemini"
        if name == "openai": display_name = "OpenAI"
        if name == "openrouter": display_name = "OpenRouter"
        if name == "ollama": display_name = "Ollama"
        if name == "groq": display_name = "Groq"
        if name == "together": display_name = "Together AI"
        if name == "mistral": display_name = "Mistral"
        if name == "custom_node": display_name = "Custom Remote Node (Tailscale/Local)"

        console.print(f"[{num}] {display_name}")

    console.print()

    provider_num = IntPrompt.ask("Enter the number of your provider", choices=[str(i) for i in PROVIDER_MAP], show_choices=False)
    provider = PROVIDER_MAP[provider_num]

    console.print(f"\n[bold green]Selected Provider:[/bold green] {provider}")

    if provider not in ["ollama", "local", "lm_studio", "vllm", "custom_node"]:
        api_key = Prompt.ask("Enter your API Key (input is hidden)", password=True)
        if api_key:
            settings = load_config()
            keys = settings.api_keys
            keys[provider] = api_key
            update_config("api_keys", keys)

    if provider in ["local", "lm_studio", "vllm"]:
        default_url = "http://localhost:8000/v1"
        if provider == "lm_studio":
            default_url = "http://localhost:1234/v1"

        base_url = Prompt.ask("Enter the base URL for the server", default=default_url)
        settings = load_config()
        urls = settings.base_urls
        urls[provider] = base_url
        update_config("base_urls", urls)
        
    if provider == "custom_node":
        from nopper.node.config import NodeConfig
        from nopper.node.manager import NodeManager, prompt_save_location
        settings = load_config()

        node_name = Prompt.ask("Enter a name for this remote node (e.g. mark_gpu)")
        while node_name in settings.nodes or NodeManager.find_node_path(node_name):
            console.print(f"[red]Node '{node_name}' already exists. Please choose a unique name.[/red]")
            node_name = Prompt.ask("Enter a name for this remote node")

        base_url = Prompt.ask("Enter the Tailscale/Remote Base URL (e.g. http://100.x.y.z:11434/v1)")
        api_key = Prompt.ask("Enter API Key (leave empty if none)", default="")

        loc_type, chosen_dir = prompt_save_location()

        node_cfg = NodeConfig(
            name=node_name,
            provider="remote" if "http" in base_url else "openai",
            base_url=base_url,
            api_key=api_key if api_key else None
        )
        saved_file = NodeManager.save(node_cfg, location=loc_type, path=str(chosen_dir))
        console.print(f"[green]Saved node '{node_name}' to:[/green] [cyan]{saved_file}[/cyan]")
        provider = node_name

    update_config("provider", provider)

    console.print(f"\n[cyan]Fetching available models for {provider}...[/cyan]")

    try:
        ai = AI()
        models = ai.models()
        if models:
            for i, m in enumerate(models, 1):
                console.print(f"[{i}] {m}")
            console.print(f"[{len(models) + 1}] Custom / Enter manually")

            model_num = IntPrompt.ask("Select your default model", choices=[str(i) for i in range(1, len(models) + 2)], show_choices=False)

            if model_num == len(models) + 1:
                model = Prompt.ask("Enter the model name exactly as required by the API")
            else:
                model = models[model_num - 1]
        else:
            console.print("[yellow]Could not automatically fetch models.[/yellow]")
            model = Prompt.ask("Enter the model name exactly as required by the API")
    except Exception as e:
        console.print(f"[yellow]Failed to fetch models:[/yellow] {e}")
        model = Prompt.ask("Enter the model name exactly as required by the API")

    update_config("model", model)

    if provider_num != 12:
        node_name = Prompt.ask("\n[bold yellow]Optional:[/bold yellow] Enter a unique name to save this configuration as a profile node (leave blank to skip)", default="")
        if node_name:
            settings = load_config()
            while node_name in settings.nodes:
                console.print(f"[red]Node '{node_name}' already exists.[/red]")
                node_name = Prompt.ask("Enter a unique name (or leave blank to skip)", default="")
                if not node_name:
                    break
                    
            if node_name:
                from nopper.config import NodeConfig, save_config
                node_type = PROVIDER_MAP[provider_num]
                node_api_key = settings.api_keys.get(node_type)
                node_base_url = settings.base_urls.get(node_type)
                
                settings.nodes[node_name] = NodeConfig(
                    type=node_type,
                    api_key=node_api_key,
                    base_url=node_base_url,
                    model=model
                )
                save_config(settings)
                console.print(f"[green]Saved configuration as node:[/green] [bold]{node_name}[/bold]")
                update_config("provider", node_name)
                provider = node_name

    console.print("\n[bold green]Setup Complete! 🎉[/bold green]")
    console.print(f"Provider: [bold]{provider}[/bold]")
    console.print(f"Default Model: [bold]{model}[/bold]")
    console.print("\n[bold cyan]You can now use Nopper in your Python code:[/bold cyan]")
    console.print("```python")
    console.print("from nopper import AI")
    console.print("ai = AI()")
    console.print("print(ai.chat('Hello!'))")
    console.print("```\n")

