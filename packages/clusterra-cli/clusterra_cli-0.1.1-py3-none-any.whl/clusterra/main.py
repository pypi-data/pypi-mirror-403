import typer
from .commands import auth, clusters, jobs, billing

app = typer.Typer(help="Clusterra CLI")

app.add_typer(auth.app, name="auth")
# We also expose `configure` and `login` at the top level for convenience
app.command(name="configure")(auth.configure)
app.command(name="login")(auth.login)

app.add_typer(clusters.app, name="clusters")
app.add_typer(jobs.app, name="jobs")
app.add_typer(billing.app, name="billing")

if __name__ == "__main__":
    app()
