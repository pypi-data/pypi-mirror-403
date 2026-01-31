import typer
from rich.table import Table
from ..api import APIClient
from ..utils import console, create_table, print_success, print_error

app = typer.Typer(help="Manage Clusterra clusters.")

@app.command()
def list():
    """List all available clusters."""
    client = APIClient()
    clusters = client.get("/v1/clusters")
    
    if not clusters:
        console.print("No clusters found.")
        return

    # Handle if API returns a list or a dict with "clusters" key
    if isinstance(clusters, dict) and "clusters" in clusters:
        clusters = clusters["clusters"]
        
    table = create_table(["ID", "Name", "State", "Status"])
    for cluster in clusters:
        # Adjust fields based on actual API response
        c_id = cluster.get("id") or cluster.get("cluster_id")
        c_name = cluster.get("name") or cluster.get("cluster_name")
        c_state = cluster.get("state") # e.g. "running"
        c_status = cluster.get("status") # e.g. "CREATE_COMPLETE"
        
        table.add_row(
            c_id or "N/A", 
            c_name or "N/A", 
            c_state or "N/A", 
            c_status or "N/A"
        )
    
    console.print(table)

@app.command()
def status(cluster_id: str):
    """Get detailed status of a cluster."""
    client = APIClient()
    cluster = client.get(f"/v1/clusters/{cluster_id}")
    console.print(cluster)

@app.command()
def start(cluster_id: str):
    """Start a cluster's head node."""
    client = APIClient()
    # API ref says POST /v1/clusters/{id}/start
    client.post(f"/v1/clusters/{cluster_id}/start")
    print_success(f"Cluster {cluster_id} start initiated.")

@app.command()
def stop(cluster_id: str, force: bool = False):
    """Stop a cluster's head node."""
    client = APIClient()
    params = {}
    if force:
        params["force"] = "true"
    
    # API ref says POST with query params, but client.post usually takes json.
    # We need to make sure our APIClient supports query params on POST or we handle it here.
    # Our APIClient.post doesn't support params kwarg in the signature I wrote.
    # I should check api.py or just append to URL.
    
    url = f"/v1/clusters/{cluster_id}/stop"
    if force:
        url += "?force=true"
        
    client.post(url)
    print_success(f"Cluster {cluster_id} stop initiated.")

@app.command()
def partitions(cluster_id: str):
    """List available partitions and their configurations."""
    client = APIClient()
    response = client.get(f"/v1/clusters/{cluster_id}/partitions")
    
    # Check if response is wrapped in "partitions" key
    if isinstance(response, dict) and "partitions" in response:
        parts = response["partitions"]
    else:
        parts = response

    if not parts:
        console.print("No partitions found.")
        return

    table = create_table(["Name", "State", "Nodes", "Max Time"])
    for p in parts:
        # Adjust fields based on potential API structure
        # Assuming structure: {name, state, node_groups: [...], max_time}
        p_name = p.get("name", "N/A")
        p_state = p.get("state", "N/A")
        p_max_time = p.get("max_time", "N/A")
        
        # Summarize node groups or count
        node_groups = p.get("node_groups", [])
        if isinstance(node_groups, list):
            nodes_info = f"{len(node_groups)} groups"
            # Maybe show instance types if few?
            types = [ng.get("instance_type") for ng in node_groups if ng.get("instance_type")]
            if types:
                nodes_info = ", ".join(types)
        else:
            nodes_info = "N/A"

        table.add_row(p_name, p_state, nodes_info, p_max_time)
    
    console.print(table)
