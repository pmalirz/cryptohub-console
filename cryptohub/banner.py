from rich.console import Console, Group
from rich.panel import Panel
from rich import box
from rich.text import Text
from rich.align import Align


def display_banner():
    """Display a beautiful banner using rich library."""
    console = Console()

    # Create styled texts
    title = Text()
    title.append("CryptoHub - Copyright (c) 2025 by ", style="yellow")
    title.append("Przemek Malirz", style="orange1")

    contact = Text("Contact: p.malirz@gmail.com", style="yellow")
    linkedin = Text("LinkedIn: https://www.linkedin.com/in/przemyslawmalirz/", style="blue underline")

    # Create a group of aligned elements
    content = Group(
        Align.center(title),
        Align.center(contact),
        Align.center(linkedin),
    )

    # Create and display panel with the grouped content
    panel = Panel(
        content,
        box=box.HEAVY,
        border_style="green",
        padding=(1, 2),
        title="[bold green]CryptoHub[/]",
        subtitle="[bold green]v1.0.3 (2025-05-02)[/]"
    )

    # Print with spacing
    console.print("\n")
    console.print(panel)
    console.print("\n")


# For testing the banner display when run directly.
if __name__ == "__main__":
    display_banner()
