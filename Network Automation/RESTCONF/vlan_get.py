import requests
from requests.auth import HTTPBasicAuth
from rich import print
from rich.panel import Panel
from rich.syntax import Syntax
import urllib3

# Disable insecure HTTPS warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Device info
device = {
    "host": "10.10.10.1",
    "port": "443",
    "username": "tmaco",
    "password": "cisco"
}

# RESTCONF headers
headers = {
    "Accept": "application/yang-data+json"
}

# Construct URL
url = f"https://{device['host']}:{device['port']}/restconf/data/Cisco-IOS-XE-native:native/vlan"

# Make the request
try:
    response = requests.get(
        url,
        headers=headers,
        auth=HTTPBasicAuth(device["username"], device["password"]),
        verify=False,
        timeout=10
    )

    if response.ok:
        print(Panel.fit(f"[bold green]Success! Status code: {response.status_code}[/bold green]"))
        print(Syntax(response.text, "json", theme="monokai", word_wrap=True))
    else:
        print(Panel.fit(f"[bold red]Failed! Status code: {response.status_code}[/bold red]"))
        print(response.text)

except requests.exceptions.RequestException as e:
    print(Panel.fit(f"[bold red]Request Error[/bold red]\n{str(e)}"))
