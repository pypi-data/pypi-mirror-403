import typer
from ..api import APIClient
from ..utils import console, create_table

app = typer.Typer(help="Check billing and usage.")

@app.command()
def current():
    """Get current usage."""
    client = APIClient()
    # API internal doc says GET /v1/usage
    usage = client.get("/v1/usage")
    console.print(usage)
