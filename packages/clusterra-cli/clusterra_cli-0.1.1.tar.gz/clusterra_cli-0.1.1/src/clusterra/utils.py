from rich.console import Console
from rich.table import Table

console = Console()

def print_error(message: str):
    console.print(f"[bold red]Error:[/bold red] {message}")

def print_success(message: str):
    console.print(f"[bold green]Success:[/bold green] {message}")

def create_table(columns: list[str]) -> Table:
    table = Table(show_header=True, header_style="bold magenta")
    for col in columns:
        table.add_column(col)
    return table
