import csv
import os
import time

import requests
from rich.console import Console
from dotenv import load_dotenv
import ipaddress

console = Console()

# Load in Env variables
load_dotenv()

fdm_host = os.getenv("FDM_HOST")
fdm_port = os.getenv("FDM_PORT")
fdm_user = os.getenv("FDM_USER")
fdm_password = os.getenv("FDM_PASSWORD")
fdm_version = os.getenv("FDM_VERSION")

# Disable warnings for insecure HTTPS requests
requests.packages.urllib3.disable_warnings()

base_url = f"https://{fdm_host}:{fdm_port}/api/fdm/{fdm_version}"


def _is_valid_ip(ip_str):
    """
    Validate if the given string is a valid IP address (IPv4 or IPv6).
    :param ip_str: String to validate
    :return: True if valid IP, False otherwise
    """
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError as e:
        console.print(f"[red]ERROR: Invalid IP address '{ip_str}: {e}'[/red]")
        return False


def _is_valid_network(ip_str):
    """
    Validate if the given string is a valid network address.
    :param ip_str: String to validate
    :return: True if valid network, False otherwise
    """
    try:
        ipaddress.ip_network(ip_str, strict=False)
        return True
    except ValueError as e:
        console.print(f"[red]ERROR: Invalid network address '{ip_str}: {e}'[/red]")
        return False


def get_token():
    global token
    url = f'{base_url}/fdm/token'
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    body = {
        'grant_type': 'password',
        'username': f'{fdm_user}',
        'password': f'{fdm_password}',
    }
    response = requests.post(url, verify=False, headers=headers, json=body)
    if response.status_code != 200:
        console.print(f"[red]ERROR: Failed to get token: {response.status_code} - {response.text}[/red]")
        return None

    # Set token globally
    token = response.json().get('access_token')

    return token


def fdm_get(token, endpoint):
    """
    Get data from FDM API
    :param token: Bearer token for authentication
    :param endpoint: API endpoint to call
    :return: JSON response data
    """
    retry_counter = 0
    all_items = []
    url = f"{base_url}/{endpoint}"

    while url and retry_counter < 5:
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'Bearer {token}'}
        response = requests.get(url, verify=False, headers=headers)
        if response.status_code != 200:
            console.print(f"[red]ERROR: API call failed: {response.status_code} - {response.text}[/red]")
            return None

        if response.status_code == 401:
            retry_counter += 1

            # Token expired, get a new one, retry call
            console.print("[yellow]Token expired, acquiring a new token...[/yellow]")
            token = get_token()
            continue

        # Check Paging
        data = response.json()
        if 'items' in data:
            items = data.get('items', [])
            all_items.extend(items)

            # Extract next URL from paging
            paging = data.get('paging', {})
            next_links = paging.get('next', [])
            url = next_links[0] if next_links else None
        else:
            return data

    return all_items


def fdm_post(token, endpoint, body):
    """
    Post data to FDM API
    :param token: Bearer token for authentication
    :param endpoint: API endpoint to call
    :param body: JSON body to send
    :return: JSON response data
    """
    url = f"{base_url}/{endpoint}"
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'Bearer {token}'}
    response = requests.post(url, verify=False, headers=headers, json=body)
    if response.status_code != 200:
        console.print(f"[red]ERROR: API call failed: {response.status_code} - {response.text}[/red]")
        return None

    return response.json()


if __name__ == "__main__":
    token = get_token()
    if token:
        console.print(f"[green]SUCCESS[/green]: Token acquired: {token}")
    else:
        console.print("[red]ERROR[/red]: Failed to acquire token")
    items = fdm_get(token, "devicesettings/default/devicehostnames")
    device_hostname = items[0].get('hostname', 'unknown') if items else 'unknown'
    if device_hostname:
        console.print(f"[green]SUCCESS[/green]: Device Hostname: {device_hostname}")

    # Get All existing network objects
    network_objects = fdm_get(token, "object/networks")
    if network_objects:
        console.print(f"[green]SUCCESS[/green]: Retrieved existing network objects:")
        console.print_json(data=network_objects)

    network_object_names = [obj['name'] for obj in network_objects]

    # Read csv, create payloads for objects in FDM format
    network_objects = []
    valid_subtypes = ["HOST", "NETWORK", "FQDN", "RANGE"]
    with open('network_objects.csv', 'r') as file:
        reader = csv.DictReader(file)

        for row in reader:
            # Check if object already exists!
            if row["Name"].strip() in network_object_names:
                console.print(f"[yellow]WARNING[/yellow]: Object '{row['Name']}' already exists, skipping...")
                continue

            obj = {
                "name": row["Name"].strip(),
                "description": row["Description"].strip(),
                "type": "networkobject"
            }

            # Check type, convert to FDM format
            subType = row['Type'].strip().upper()
            if subType not in valid_subtypes:
                console.print(f"[red]ERROR[/red]: Invalid type '{subType}' for object '{row['Name']}'")
                continue

            obj['subType'] = subType

            # Validate object value conforms to rules of FDM
            if subType == "HOST":
                value = row["Value"].strip()

                if '/' in value:
                    console.print(f"[red]ERROR[/red]: Invalid value '{obj['value']}' for object '{row['Name']}'. Must be a single IP address!")
                    continue

                if _is_valid_ip(value):
                    obj['value'] = value
                else:
                    console.print(f"[red]ERROR[/red]: Invalid IP address '{value}' for object '{row['Name']}'")
                    continue

            elif subType == "NETWORK":
                value = row["Value"].strip()

                if '/' not in value:
                    console.print(f"[red]ERROR[/red]: Invalid value '{obj['value']}' for object '{row['Name']}'. Must be a network address!")
                    continue

                if _is_valid_network(value):
                    obj['value'] = value
                else:
                    console.print(f"[red]ERROR[/red]: Invalid network address '{value}' for object '{row['Name']}'")
                    continue

            elif subType == "FQDN":
                value = row["Value"].strip()
                obj['value'] = value
            else:
                # RANGE Case
                value = row["Value"].strip()

                if '-' not in value:
                    console.print(f"[red]ERROR[/red]: Invalid value '{obj['value']}' for object '{row['Name']}'. Must be a range!")
                    continue

                start, end = value.split('-')
                start = start.strip()
                end = end.strip()

                if _is_valid_ip(start) and _is_valid_ip(end):
                    obj['value'] = f"{start}-{end}"
                else:
                    console.print(f"[red]ERROR[/red]: Invalid range '{value}' for object '{row['Name']}'")
                    continue

            network_objects.append(obj)

    # Add network objects to FDM
    for obj in network_objects:
        response = fdm_post(token, "object/networks", obj)

        if response:
            console.print(f"[green]SUCCESS[/green]: Created network object '{obj}'")

    # Deploy configuration changes to FDM
    response = fdm_post(token, "operational/deploy", {})

    if response:
        console.print(f"[green]SUCCESS[/green]: Deployment initiated with ID: {response['id']}")

        # Check if deployment was successful
        state = response['state']
        obj_id = response['id']
        while True:
            # Break on success
            if state == 'DEPLOYED':
                console.print("[green]SUCCESS[/green]: Configuration deployed successfully!")
                break
            elif state in ['DEPLOY_FAILED', 'DEPLOY_TIMEOUT']:
                console.print(f"[red]ERROR[/red]: Deployment failed with state '{state}'")
                break

            # Get current state of deployment object
            response = fdm_get(token, f"operational/deploy/{obj_id}")
            if response:
                console.print(f"[yellow]INFO[/yellow]: Current State of job id {obj_id} - {state}")
                state = response['state']
            else:
                # Some failure, break infinite loop
                break

            # sleep for a while before checking again
            time.sleep(2)
