import requests
import urllib3
from rich import print
from rich.panel import Panel

# Suppress HTTPS warnings for self-signed certs
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
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json"
}

# URL to PATCH VLAN configuration
url = f"https://{device['host']}:{device['port']}/restconf/data/Cisco-IOS-XE-native:native/vlan"

# Payload to add VLAN 100 with name "MGMT_VLAN"
payload = {
    "Cisco-IOS-XE-native:vlan": {
        "Cisco-IOS-XE-vlan:vlan-list": [
            {
                "id": 100,
                "name": "MGMT_VLAN"
            }
        ]
    }
}

# Perform PATCH operation
try:
    response = requests.patch(
        url=url,
        headers=headers,
        auth=(device['username'], device['password']),
        json=payload,
        verify=False
    )

    if response.ok:
        print(Panel.fit(f"[bold green]Success! VLAN 100 configured[/bold green]\nStatus Code: {response.status_code}"))
    else:
        print(Panel.fit(f"[bold red]Error![/bold red] Status Code: {response.status_code}\n{response.text}"))

except requests.exceptions.RequestException as err:
    print(Panel.fit(f"[bold red]Request failed:[/bold red] {err}"))
