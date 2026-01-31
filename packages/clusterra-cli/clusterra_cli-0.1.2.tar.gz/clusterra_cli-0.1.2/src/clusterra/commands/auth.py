import typer
import time
import webbrowser
import uvicorn
import threading
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from ..config import load_config, save_config, Config
from ..utils import print_success, print_error, console

app = typer.Typer()

# Fixed for now to match Google Console requirement
REDIRECT_PORT = 8000
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"
# Extracted from .env.deployed / terraform.tfvars
GOOGLE_CLIENT_ID = "128955612318-as9vf78r6i8ptejtmdtj8deb5kd1orip.apps.googleusercontent.com"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"

@app.command()
def login():
    """
    Log in via Google OIDC (Browser).
    """
    config = load_config()
    if not config.api_url:
        print_error("Please run 'clusterra configure --url <URL>' first to set API URL.")
        raise typer.Exit(1)

    print_success("Launching browser for authentication...")
    
    # Generate Auth URL (Implicit Flow used for simplicity with Web Client ID)
    # We use response_type=id_token + token to get both, but we mostly need id_token for API.
    # Note: 'token' gives access_token, 'id_token' gives JWT. 
    # API Gateway expects 'id_token' in Authorization header (OIDC).
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "id_token",
        "scope": "email profile openid",
        "nonce": str(time.time()), # Simple nonce
    }
    import urllib.parse
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    # Start local server to capture token
    token_container = {}
    server_thread = threading.Thread(target=_start_callback_server, args=(token_container,), daemon=True)
    server_thread.start()
    
    # Give server a moment to start
    time.sleep(1)
    
    # Open Browser
    webbrowser.open(url)
    console.print(f"Waiting for authentication... (listening on {REDIRECT_URI})")
    
    # Wait for token
    for _ in range(60): # Wait up to 60s
        if "token" in token_container:
            config.api_token = token_container["token"]
            save_config(config)
            print_success("Successfully logged in!")
            return
        time.sleep(1)
        
    print_error("Authentication timed out.")
    raise typer.Exit(1)

def _start_callback_server(container):
    """Starts a temporary FastAPI server to handle the redirect."""
    fast_app = FastAPI()
    
    # 1. Google redirects here with #id_token=... (Fragment)
    # 2. Server sends HTML with JS to extract fragment and POST to /save
    @fast_app.get("/callback")
    def callback():
        return HTMLResponse("""
        <html>
            <body>
                <h1>Authenticating...</h1>
                <script>
                    const hash = window.location.hash.substring(1);
                    const params = new URLSearchParams(hash);
                    const id_token = params.get('id_token');
                    
                    if (id_token) {
                        fetch('/save', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({token: id_token})
                        }).then(() => {
                            document.body.innerHTML = '<h1>Login Successful! You can close this window.</h1>';
                        });
                    } else {
                        document.body.innerHTML = '<h1>Login Failed. No token found.</h1>';
                    }
                </script>
            </body>
        </html>
        """)

    @fast_app.post("/save")
    async def save_token(request: Request):
        data = await request.json()
        container["token"] = data.get("token")
        return {"status": "ok"}

    # Run silently
    try:
        uvicorn.run(fast_app, host="localhost", port=REDIRECT_PORT, log_level="critical")
    except Exception:
        pass # Server might be killed or port in use

@app.command()
def configure(
    url: str = typer.Option(None, prompt="Clusterra API URL"),
    token: str = typer.Option(None, prompt="API Token (Bearer)", hide_input=True),
):
    """
    Configure Clusterra CLI settings.
    """
    config = load_config()
    
    if url:
        config.api_url = url.rstrip("/")
    if token:
        config.api_token = token
        
    save_config(config)
    print_success("Configuration saved.")
