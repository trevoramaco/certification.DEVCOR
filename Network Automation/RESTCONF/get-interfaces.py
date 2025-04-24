import requests
import urllib3
from requests.exceptions import RequestException, Timeout
from rich.console import Console
from rich.panel import Panel
from rich.pretty import pprint

# Disable InsecureRequestWarning (for verify=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize console
console = Console()

# Device information
device = {
    "host": "10.10.10.1",
    "port": "443",
    "username": "tmaco",
    "password": "cisco"
}

# RESTCONF headers
headers = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json"
}

# Construct full URL (comes from yang model, interfaces is a List)
url = f"https://{device['host']}:{device['port']}/restconf/data/ietf-interfaces:interfaces"


def get_interfaces():
    """
    Send a GET request to the RESTCONF API to retrieve interface information.
    """
    console.print(f"[cyan]Sending RESTCONF request to:[/cyan] [bold]{url}[/bold]")

    try:
        response = requests.get(
            url=url,
            headers=headers,
            auth=(device["username"], device["password"]),
            verify=False,
            timeout=10
        )

        if response.ok:
            console.print(Panel.fit("[green]✅ Request successful![/green]", title="Status"))
            pprint(response.json())
        else:
            console.print(
                Panel.fit(
                    f"[red]❌ Request failed[/red]\n[bold]Status Code:[/bold] {response.status_code}\n[bold]Response:[/bold] {response.text}",
                    title="Error"
                )
            )

    except Timeout:
        console.print("[bold red]⏱️ Request timed out[/bold red]")
    except RequestException as err:
        console.print(f"[bold red]🚨 Exception occurred:[/bold red] {err}")


# Run the function
if __name__ == "__main__":
    get_interfaces()
