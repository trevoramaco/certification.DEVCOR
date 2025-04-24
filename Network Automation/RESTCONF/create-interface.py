import json
import requests
import urllib3
from requests.exceptions import RequestException, Timeout
from rich.console import Console
from rich.panel import Panel

# Disable HTTPS warning due to verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console()

# Device info
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

# Construct RESTCONF URL for interfaces
url = f"https://{device['host']}:{device['port']}/restconf/data/ietf-interfaces:interfaces"

# Payload to create a Loopback interface
payload = {
    "ietf-interfaces:interface": {
        "name": "Loopback100",
        "description": "Added by CBT Nuggets",
        "type": "iana-if-type:softwareLoopback",
        "enabled": True,
        "ietf-ip:ipv4": {
            "address": [
                {
                    "ip": "172.16.100.1",
                    "netmask": "255.255.255.0"
                }
            ]
        }
    }
}


def create_interface():
    """
    Send a POST request to the RESTCONF API to create a new interface.
    """
    console.print(f"[cyan]Sending POST request to:[/cyan] [bold]{url}[/bold]")

    try:
        response = requests.post(
            url=url,
            headers=headers,
            auth=(device["username"], device["password"]),
            data=json.dumps(payload),
            verify=False,
            timeout=10
        )

        if response.ok:
            console.print(Panel.fit("[green]✅ Interface successfully created![/green]", title="Success"))
            if response.text:
                console.print_json(response.text)
            else:
                console.print("[grey]No response body returned.[/grey]")
        else:
            console.print(Panel.fit(
                f"[red]❌ Request failed[/red]\n"
                f"[bold]Status Code:[/bold] {response.status_code}\n"
                f"[bold]Response:[/bold]\n{response.text}",
                title="RESTCONF Error"
            ))

    except Timeout:
        console.print("[bold red]⏱️ Request timed out[/bold red]")
    except RequestException as err:
        console.print(f"[bold red]🚨 Request exception:[/bold red] {err}")


if __name__ == "__main__":
    create_interface()
