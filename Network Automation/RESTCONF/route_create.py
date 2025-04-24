import requests
import urllib3
from rich import print
from rich.panel import Panel
from rich.pretty import pprint

# Suppress SSL warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Device connection info
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

# Endpoint to patch static routes
url = f"https://{device['host']}:{device['port']}/restconf/data/Cisco-IOS-XE-native:native/ip/route"

# Static route payload
payload = {
    "Cisco-IOS-XE-native:route": {
        "ip-route-interface-forwarding-list": [
            {
                "prefix": "192.168.10.0",
                "mask": "255.255.255.0",
                "fwd-list": [
                    {
                        "fwd": "GigabitEthernet1"
                    }
                ]
            }
        ]
    }
}

# Send PATCH request
try:
    response = requests.patch(
        url=url,
        headers=headers,
        auth=(device['username'], device['password']),
        json=payload,
        verify=False
    )

    if response.ok:
        print(Panel.fit(f"[bold green]Route added successfully![/bold green] Status code: {response.status_code}", title="PATCH /ip/route"))
        if response.text:
            pprint(response.json())
    else:
        print(Panel.fit(f"[bold red]Failed to add route[/bold red] Status code: {response.status_code}", title="PATCH /ip/route"))
        print(response.text)

except requests.exceptions.RequestException as e:
    print(Panel.fit(f"[bold red]Request Error:[/bold red] {e}", title="Exception"))
