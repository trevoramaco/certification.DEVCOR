import requests
import urllib3
from rich import print
from rich.panel import Panel
from rich.pretty import pprint

# Suppress TLS certificate warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Device connection details
device = {
    "host": "10.10.10.1",
    "port": "443",
    "username": "tmaco",
    "password": "cisco"
}

# RESTCONF headers
headers = {
    "Accept": "application/yang-data+json",
}

# RESTCONF URL for static route config
url = f"https://{device['host']}:{device['port']}/restconf/data/Cisco-IOS-XE-native:native/ip/route"

# Perform GET request
try:
    response = requests.get(url=url, headers=headers, auth=(device['username'], device['password']), verify=False)

    if response.ok:
        print(Panel.fit(f"[bold green]Success![/bold green] Status code: {response.status_code}", title="GET /ip/route"))
        try:
            pprint(response.json())
        except ValueError:
            print("[yellow]Warning:[/yellow] Response is not valid JSON.")
            print(response.text)
    else:
        print(Panel.fit(f"[bold red]Request Failed[/bold red] Status code: {response.status_code}", title="GET /ip/route"))
        print(response.text)

except requests.exceptions.RequestException as e:
    print(Panel.fit(f"[bold red]Error:[/bold red] {e}", title="Request Error"))
