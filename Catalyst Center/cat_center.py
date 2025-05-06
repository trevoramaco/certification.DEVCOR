import json
import time

from dotenv import load_dotenv
from requests import RequestException
from rich.console import Console
import requests
import os

from rich.prompt import Prompt, Confirm
from rich.table import Table

# Rich console
console = Console()

# Load in Env variables
load_dotenv()

CAT_CENTER_HOST = os.getenv("CAT_CENTER_HOST")
CAT_CENTER_USER = os.getenv("CAT_CENTER_USER")
CAT_CENTER_PASSWORD = os.getenv("CAT_CENTER_PASSWORD")

# Disable warnings for insecure HTTPS requests
requests.packages.urllib3.disable_warnings()


class CAT_CENTER:
    """
    Class to interact with Cisco Catalyst Center API (no SDK)
    """

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.base_url = f"https://{self.host}/dna/intent/api/v1"
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification (adjust as needed)
        self.token = None
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Auth-Token": self.token
        }

    def _request(self, method, endpoint, data=None, params=None, auto_retry=True):
        """
        Internal helper to send HTTP requests, check HTTP status, parse JSON, and handle errors
        :param method: "GET", "POST", "PUT", "DELETE"
        :param endpoint: API endpoint (e.g., "network-device")
        :param data: JSON body for POST/PUT requests
        :param params: URL parameters
        :param auto_retry: Retry on 401 Unauthorized
        :return: Parsed JSON response or raw text
        """
        url = f"{self.base_url}/{endpoint}"
        self.headers["X-Auth-Token"] = self.token  # Always update in case it changed

        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                headers=self.headers,
                json=data,
                params=params
            )
        except RequestException as e:
            raise Exception(f"Request failed: {e}")

        # Handle unauthorized error (trigger re-auth once)
        if response.status_code == 401 and auto_retry:
            console.print("[yellow]Token expired, re-authenticating...[/]")
            self.login()
            return self._request(method, endpoint, data, params, auto_retry=False)

        if response.status_code >= 400:
            raise Exception(f"HTTP {response.status_code} Error: {response.text}")

        # Attempt JSON decode
        try:
            result = response.json()
        except json.JSONDecodeError:
            console.print(f"[red]Failed to decode JSON response:[/] {response.text}")
            return response.text

        # Warning: no pagination handling in this example (requires offset and a count to know how many pages there are)

        return result

    def login(self):
        """
        Authenticate with Catalyst Center and store the token
        """
        url = f"https://{self.host}/dna/system/api/v1/auth/token"
        response = self.session.post(url, auth=(self.username, self.password), headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"Login failed: {response.status_code} - {response.text}")

        self.token = response.json()["Token"]
        self.headers["X-Auth-Token"] = self.token
        console.print(f"[green]Authenticated with Catalyst Center[/]: {self.token}")

    def get_network_device_list(self):
        """
        Get a list of all compute blades
        """
        endpoint = "network-device"

        # Request all network devices
        devices = self._request("GET", endpoint)['response']

        table = Table(title="Catalyst Center - Network Devices")

        columns = ["Hostname", "Mgmt IP", "Serial", "Version", "Platform", "Role", "Uptime", "Status"]
        for col in columns:
            table.add_column(col, style="cyan")

        for device in devices:
            table.add_row(
                device.get('hostname', 'N/A'),
                device.get('managementIpAddress', 'N/A'),
                device.get('serialNumber', 'N/A'),
                device.get('softwareVersion', 'N/A'),
                device.get('platformId', 'N/A'),
                device.get('role', 'N/A'),
                device.get('upTime', 'N/A'),
                device.get('reachabilityStatus', 'N/A')
            )

        console.print(table)

        return devices

    def get_topology(self):
        """
        Get the physical and logical topology
        """
        # === Site Topology ===
        site_endpoint = "topology/site-topology"
        site_response = self._request("GET", site_endpoint)['response']

        site_table = Table(title="Site Topology", show_lines=True)
        site_table.add_column("Site Name", style="bold")
        site_table.add_column("Group Hierarchy", style="dim")

        for site in site_response['sites']:
            site_table.add_row(site['name'], site.get('groupNameHierarchy', 'N/A'))

        console.print(site_table)

        # === Physical Topology ===
        physical_endpoint = "topology/physical-topology"
        physical_response = self._request("GET", physical_endpoint)['response']

        # Create node ID to label map
        nodes = {node['id']: node['label'] for node in physical_response['nodes']}

        # Build link table
        link_table = Table(title="Physical Topology Links", show_lines=True)
        link_table.add_column("Source Device", style="cyan")
        link_table.add_column("Src Port", style="magenta")
        link_table.add_column("Target Device", style="cyan")
        link_table.add_column("Target Port", style="magenta")
        link_table.add_column("Link Status", style="green")

        for link in physical_response['links']:
            source_label = nodes.get(link['source'], "Unknown")
            target_label = nodes.get(link['target'], "Unknown")
            link_table.add_row(
                source_label,
                link.get('startPortName', 'N/A'),
                target_label,
                link.get('endPortName', 'N/A'),
                link.get('linkStatus', 'Unknown')
            )

        console.print(link_table)

    def get_site_health(self):
        """
        Get the site health summary
        """
        endpoint = "site-health"

        # Request all network devices
        site_health_data = self._request("GET", endpoint)['response']

        table = Table(title="Site Health Summary")

        # Define table columns
        table.add_column("Site Name", style="bold")
        table.add_column("Type")
        table.add_column("Access Health (%)", justify="right")
        table.add_column("Switch Health (%)", justify="right")
        table.add_column("Router Health (%)", justify="right")
        table.add_column("AP Health (%)", justify="right")
        table.add_column("Network Health (Avg %)", justify="right")
        table.add_column("Devices (Good / Total)", justify="right")
        table.add_column("Switches", justify="right")
        table.add_column("Routers", justify="right")
        table.add_column("APs", justify="right")

        for site in site_health_data:
            def fmt(good, total):
                return f"{good or 0} / {total or 0}"

            table.add_row(
                site.get("siteName", "N/A"),
                site.get("siteType", "N/A"),
                str(site.get("networkHealthAccess", "N/A")),
                str(site.get("networkHealthSwitch", "N/A")),
                str(site.get("networkHealthRouter", "N/A")),
                str(site.get("networkHealthAP", "N/A")),
                str(site.get("networkHealthAverage", "N/A")),
                fmt(site.get("accessGoodCount"), site.get("accessTotalCount")),
                fmt(site.get("switchDeviceGoodCount"), site.get("switchDeviceTotalCount")),
                fmt(site.get("routerGoodCount"), site.get("routerTotalCount")),
                fmt(site.get("apDeviceGoodCount"), site.get("apDeviceTotalCount")),
            )

        console.print(table)

    def execute_command_runner(self):
        """
        Execute a command via the Command Runner API
        """
        # Step 1: Fetch all network devices
        devices = self.get_network_device_list()
        if not devices:
            console.print("[red]No devices found.[/]")
            return

        # Step 2: Show devices in a table
        console.print("\n[bold green]Available Devices:[/bold green]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Index", style="dim", width=6)
        table.add_column("Hostname")
        table.add_column("Mgmt IP")
        table.add_column("UUID")

        for idx, dev in enumerate(devices, 1):
            table.add_row(str(idx), dev.get("hostname", "N/A"), dev.get("managementIpAddress", "N/A"), dev["id"])
        console.print(table)

        # Step 3: Select one or more device indices
        selected_indices = Prompt.ask("Enter device indices (comma-separated)", default="1").split(",")
        try:
            selected_indices = [int(i.strip()) for i in selected_indices]
            selected_uuids = [devices[i]["id"] for i in selected_indices]
        except (ValueError, IndexError):
            console.print("[red]Invalid input.[/]")
            return

        # Step 4: Input commands
        commands = []
        while True:
            cmd = Prompt.ask("Enter a CLI command")
            commands.append(cmd)
            if not Confirm.ask("Add another command?", default=False):
                break

        # Step 5: Run the commands
        endpoint = "network-device-poller/cli/read-request"
        payload = {
            "name": "Command Runner via API",
            "commands": commands,
            "deviceUuids": selected_uuids
        }

        response = self._request("POST", endpoint, data=payload)['response']

        # Monitor the command execution status
        if 'taskId' in response:
            task_id = response['taskId']
            console.print(f"[yellow]Task ID: [/] {response['taskId']}")
        else:
            console.print("[red]Failed to execute command.[/]")
            return

        # Step 6: Poll for results
        console.print("[yellow]Polling for task completion...[/]")
        progress = {}
        for _ in range(10):
            time.sleep(2)  # Wait between polls
            task_result = self._request("GET", f"task/{task_id}")['response']  # Adjust prefix if needed

            isError = task_result.get("isError", False)
            endTime = task_result.get("endTime", None)

            if not isError and endTime:
                progress = task_result.get("progress", {})
                console.print(f"[green]Task completed successfully![/]")
                break

        # Step 7: Retrieve output via fileId
        file_id = json.loads(progress).get("fileId", "")

        if not file_id:
            console.print("[red]No fileId found in task result![/]")
            return

        file_output = self._request("GET", f"file/{file_id}")

        console.print("[green]Command Output:[/green]")
        for device in file_output:
            hostname = device.get("deviceUuid", "Unknown Device")
            command_outputs = device.get("commandResponses", {}).get("SUCCESS", {})

            console.rule(f"[blue]Device UUID: {hostname}[/]")
            for cmd, output in command_outputs.items():
                console.print(output)

    def path_trace(self):
        """
        Perform a path trace
        """
        # Step 1: Fetch all network devices
        devices = self.get_network_device_list()
        if not devices:
            console.print("[red]No devices found.[/]")
            return

        # Step 2: Show devices in a table
        console.print("\n[bold green]Available Devices:[/bold green]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Index", style="dim", width=6)
        table.add_column("Hostname")
        table.add_column("Mgmt IP")
        table.add_column("UUID")

        for idx, dev in enumerate(devices, 1):
            table.add_row(str(idx), dev.get("hostname", "N/A"), dev.get("managementIpAddress", "N/A"), dev["id"])
        console.print(table)

        # Step 3: Select one or more device indices
        selected_index = Prompt.ask("Select a source device (by index)", default="1",
                                    choices=[str(i) for i in range(1, len(devices) + 1)])
        src_ip = devices[int(selected_index) - 1]["managementIpAddress"]

        # Step 4: Input destination IP address
        selected_index = Prompt.ask("Select a dest device (by index)", default="2",
                                    choices=[str(i) for i in range(1, len(devices) + 1)])
        dest_ip = devices[int(selected_index) - 1]["managementIpAddress"]

        # Step 5: Run the path trace
        endpoint = "flow-analysis"
        payload = {
            "sourceIP": src_ip,
            "destIP": dest_ip,
            'inclusions': [
                'INTERFACE-STATS',
                'DEVICE-STATS',
                'ACL-TRACE',
                'QOS-STATS'
            ],
            'protocol': 'icmp'
        }

        response = self._request("POST", endpoint, data=payload)['response']
        flow_analysis_id = response['flowAnalysisId']
        task_id = response['taskId']

        # Step 6: Poll for results
        console.print("[yellow]Polling for task completion...[/]")
        for _ in range(10):
            time.sleep(2)  # Wait between polls
            task_result = self._request("GET", f"task/{task_id}")['response']  # Adjust prefix if needed

            isError = task_result.get("isError", False)
            endTime = task_result.get("endTime", None)

            if not isError and endTime:
                task_id = task_result.get("progress", "")
                console.print(f"[green]Task completed successfully![/]")
                break

        # Step 7: Retrieve path trace results
        if task_id == flow_analysis_id:
            # Success!
            console.print("[green]Path Trace Results:[/green]")
            path_trace_result = self._request("GET", f"flow-analysis/{flow_analysis_id}")['response']
            console.print(json.dumps(path_trace_result, indent=4))


def main_menu(cat_center):
    """
    Main menu to select exercises
    """
    # # === Exercise Menu ===
    exercises = {
        "1": ("Query all Network Devices", cat_center.get_network_device_list),
        "2": ("Execute Command via Command Runner", cat_center.execute_command_runner),
        "3": ("Get Site Health", cat_center.get_site_health),
        "4": ("Path Trace", cat_center.path_trace),
        "5": ("Get Physical, Logical Topology", cat_center.get_topology),
        # Add more entries as needed
    }

    console.print("\n[bold green]Select an Exercise to Run:[/bold green]")
    for key, (desc, _) in exercises.items():
        console.print(f"[cyan]{key}.[/] {desc}")

    choice = Prompt.ask("\nEnter your choice", choices=list(exercises.keys()), default="1")
    _, func = exercises[choice]
    func()


if __name__ == "__main__":
    cat_center = CAT_CENTER(CAT_CENTER_HOST, CAT_CENTER_USER, CAT_CENTER_PASSWORD)

    # Login to Catalyst Center
    cat_center.login()

    try:
        # Run the main menu
        main_menu(cat_center)
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
