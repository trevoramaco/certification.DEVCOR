from datetime import datetime
import pytz

from flask import Flask, request
from dotenv import load_dotenv
import os
from rich.pretty import pprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Flask Config
app = Flask(__name__)

console = Console()

# Load environment variables from .env file
load_dotenv()

# MERAKI SETTINGS
validator = os.getenv('VALIDATOR')
secret = os.getenv('SECRET')
version = "3.0"

# Store MACs with their last seen timestamp
mac_last_seen = {}

# Define timezone
eastern = pytz.timezone("US/Eastern")


@app.route("/", methods=["GET"])
def get_validator():
    """
    Returns the validator string for the Meraki webhook. Required to validate API connection to Flask App
    :return: validator string
    """
    return validator


@app.route("/", methods=["POST"])
def get_locationJSON():
    """
    Receives the JSON data from the Meraki Location API and verifies the secret and version. Displays the data in the console.
    :return: success message
    """
    global mac_last_seen

    data = request.json

    # Check if the request contains JSON data
    if not request.json or "data" not in request.json:
        console.log("[bold red]❌ Invalid data structure[/bold red]")
        return "invalid data", 400

    # Validate secret
    incoming_secret = data.get("secret", "")
    if incoming_secret != secret:
        console.log(f"[bold red]❌ Invalid secret:[/bold red] {incoming_secret}")
        return "invalid secret", 403
    else:
        console.log(f"[green]✅ Secret verified:[/green] {incoming_secret}")

    # Validate version
    incoming_version = data.get("version", "")
    if incoming_version != version:
        console.log(f"[bold red]❌ Invalid version:[/bold red] {incoming_version}")
        return "invalid version", 400
    else:
        console.log(f"[green]✅ Version verified:[/green] {incoming_version}")

    # Handle device type
    device_type = data.get("type")
    if device_type == "WiFi":
        console.log("[yellow]📶 WiFi Devices Seen[/yellow]")
    elif device_type == "BLE":
        console.log("[blue]🔵 Bluetooth Devices Seen[/blue]")
    else:
        console.log(f"[red]❓ Unknown device type:[/red] {device_type}")
        return "invalid device type", 403

    # Rich preview of incoming payload
    console.print(Panel.fit("📡 [bold green]Location Scanning Payload Received[/bold green]", style="bold cyan"))
    pprint(data)

    # Fun Use Case: Track all unique MACs with timestamp of last seen
    observations = data["data"].get("observations", [])

    # Current time in EST
    now_est = datetime.now(pytz.utc).astimezone(eastern)
    readable_time = now_est.strftime("%-m/%-d/%Y (%-I:%M %p)")

    new_macs = 0
    for obs in observations:
        mac = obs.get("clientMac")
        if not mac:
            continue
        if mac not in mac_last_seen:
            new_macs += 1
        mac_last_seen[mac] = readable_time

    # Build a full table of all seen devices
    table = Table(title="📋 All Devices Seen", show_lines=True)
    table.add_column("MAC Address", style="cyan")
    table.add_column("Last Seen At", style="magenta")

    for mac, timestamp in sorted(mac_last_seen.items()):
        table.add_row(mac, timestamp)

    console.print(table)

    # Return success message
    return "Location Scanning POST Received", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
