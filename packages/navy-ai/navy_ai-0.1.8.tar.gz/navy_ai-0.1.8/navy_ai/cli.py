import typer
from typing import Optional
from rich.console import Console
from navy_ai.providers import load_provider

app = typer.Typer(
    add_completion=False,
    invoke_without_command=True,
    help="Navy AI — terminal-first AI assistant",
)

console = Console()


@app.callback()
def main(
    ctx: typer.Context,
    prompt: Optional[str] = typer.Argument(
        None,
        help="Prompt to send to the AI (omit to enter interactive mode)",
    ),
    provider: str = typer.Option(
        "ollama",
        "--provider",
        "-p",
        help="AI provider: ollama | gemini | openai",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Model name for the selected provider",
    ),
):
    try:
        ai = load_provider(provider, model)

        if prompt:
            console.print(ai.chat(prompt))
        else:
            interactive(ai)

    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")


def interactive(ai):
    while True:
        try:
            prompt = console.input("[bold cyan]Navy AI > [/]")
            if prompt.lower() in ("exit", "quit"):
                break
            console.print(ai.chat(prompt))
        except RuntimeError as e:
            console.print(f"[red]{e}[/red]")
        except KeyboardInterrupt:
            console.print("\nExiting Navy AI.")
            break


if __name__ == "__main__":
    app()
