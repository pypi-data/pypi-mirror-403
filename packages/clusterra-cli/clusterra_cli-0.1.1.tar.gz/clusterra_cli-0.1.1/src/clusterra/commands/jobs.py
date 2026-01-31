import typer
from pathlib import Path
from ..api import APIClient
from ..utils import console, create_table, print_success, print_error

app = typer.Typer(help="Manage HPC jobs.")

@app.command()
def list(cluster_id: str = typer.Option(..., "--cluster-id", "-c", help="Cluster ID")):
    """List jobs on a cluster."""
    client = APIClient()
    # API: GET /v1/clusters/{cluster_id}/jobs
    jobs = client.get(f"/v1/clusters/{cluster_id}/jobs")
    
    if not jobs:
        console.print("No jobs found.")
        return
        
    if isinstance(jobs, dict) and "jobs" in jobs:
        jobs = jobs["jobs"]
        
    table = create_table(["Job ID", "Name", "State", "Partition", "Note"])
    for job in jobs:
        # Adjust fields
        j_id = str(job.get("job_id", "N/A"))
        j_name = job.get("name", "N/A")
        j_state = job.get("state", "N/A")
        j_part = job.get("partition", "N/A")
        
        table.add_row(j_id, j_name, j_state, j_part)
        
    console.print(table)

@app.command()
def submit(
    cluster_id: str = typer.Option(..., "--cluster-id", "-c", help="Cluster ID"),
    script: Path = typer.Option(..., exists=True, dir_okay=False, help="Path to job script"),
    name: str = typer.Option(None, help="Job name"),
    partition: str = typer.Option("compute", help="Partition to submit to"),
    cpus: int = typer.Option(1, help="Number of CPUs"),
    memory: int = typer.Option(1, help="Memory in GB"),
    gpus: int = typer.Option(0, help="Number of GPUs"),
    time_limit: str = typer.Option("01:00:00", help="Time limit (HH:MM:SS)"),
):
    """Submit a job to a cluster."""
    client = APIClient()
    
    try:
        script_content = script.read_text()
    except Exception as e:
        print_error(f"Failed to read script file: {e}")
        raise typer.Exit(1)
        
    payload = {
        "name": name or script.stem,
        "script": script_content,
        "partition": partition,
        "cpus": cpus,
        "memory_gb": memory,
        "gpus": gpus,
        "time_limit": time_limit,
        "auto_start": True
    }
    
    response = client.post(f"/v1/clusters/{cluster_id}/jobs", json=payload)
    
    # Assuming response contains job_id
    job_id = response.get("job_id")
    if job_id:
        print_success(f"Job submitted successfully. Job ID: {job_id}")
    else:
        print_success("Job submitted successfully.")
        console.print(response)

@app.command()
def get(
    job_id: str,
    cluster_id: str = typer.Option(..., "--cluster-id", "-c", help="Cluster ID")
):
    """Get job details."""
    client = APIClient()
    job = client.get(f"/v1/clusters/{cluster_id}/jobs/{job_id}")
    console.print(job)

@app.command()
def cancel(
    job_id: str,
    cluster_id: str = typer.Option(..., "--cluster-id", "-c", help="Cluster ID")
):
    """Cancel a job."""
    client = APIClient()
    client.delete(f"/v1/clusters/{cluster_id}/jobs/{job_id}")
    print_success(f"Job {job_id} cancelled.")

@app.command()
def logs(
    job_id: str,
    cluster_id: str = typer.Option(..., "--cluster-id", "-c", help="Cluster ID")
):
    """Get job logs (output)."""
    client = APIClient()
    # API: GET /v1/clusters/{cluster_id}/jobs/{job_id}/output
    output = client.get(f"/v1/clusters/{cluster_id}/jobs/{job_id}/output")
    
    # If it's pure text, print it. If json, print json.
    console.print(output)
