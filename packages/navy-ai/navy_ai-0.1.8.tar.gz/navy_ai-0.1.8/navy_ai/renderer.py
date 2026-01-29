from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

def render(text: str) -> None:
    md = Markdown(text)
    panel = Panel(
        md,
        title="Navy AI",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)
