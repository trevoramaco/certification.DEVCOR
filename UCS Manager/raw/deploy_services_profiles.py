import argparse
import os
from xml.dom import minidom

import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from rich.console import Console
from rich.syntax import Syntax

# Rich console
console = Console()

# Load in Env variables
load_dotenv()

UCS_HOST = os.getenv("UCS_HOST")
UCS_USER = os.getenv("UCS_USER")
UCS_PASSWORD = os.getenv("UCS_PASSWORD")

# Disable warnings for insecure HTTPS requests
requests.packages.urllib3.disable_warnings()


def print_xml(xml_string: str):
    """
    Pretty print XML with indentation and syntax highlighting
    """
    try:
        parsed = minidom.parseString(xml_string)
        pretty = parsed.toprettyxml(indent="  ")
        syntax = Syntax(pretty, "xml", theme="monokai", line_numbers=True)
        console.print(syntax)
    except Exception as e:
        console.print(f"[red]Failed to pretty-print XML:[/] {e}")
        console.print(xml_string)


class UCS:
    """
    Class to interact with Cisco UCS Manager API (raw XML, no SDK)
    """

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.cookie = None
        self.base_url = f"https://{self.host}/nuova"
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification (adjust as needed)
        self.headers = {
            "Content-Type": "application/xml"
        }

    def _send_request(self, body):
        """
        Internal helper to send XML body, check HTTP, parse XML, and raise UCSM errors
        """
        # POST request to base URL (UCS Manager)
        try:
            response = self.session.post(self.base_url, headers=self.headers, data=body)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")

        # Check for HTTP error
        if response.status_code != 200:
            raise Exception(f"HTTP Error: {response.status_code} - {response.text}")

        # Parse XML Response
        try:
            root = ET.fromstring(response.text)
        except ET.ParseError as e:
            raise Exception(f"Failed to parse XML: {e}")

        # Check for UCSM error
        if root.tag == "error":
            error_descr = root.attrib.get("errorDescr", "Unknown error")
            error_code = root.attrib.get("errorCode", "Unknown code")
            raise Exception(f"UCSM Error [{error_code}]: {error_descr}")

        return root

    def login(self):
        """
        Login to UCS Manager and retrieve the cookie
        """
        body = f'<aaaLogin inName="{self.username}" inPassword="{self.password}"/>'
        root = self._send_request(body)

        self.cookie = root.attrib.get('outCookie')
        console.print(f"[green]Login successful! Cookie:[/] {self.cookie}")
        return self.cookie

    def logout(self):
        """
        Logout from UCS Manager
        """
        body = f'<aaaLogout inCookie="{self.cookie}"/>'
        self._send_request(body)
        console.print("[green]Logout successful![/]")

    def config_resolve_class(self, classId):
        """
        Resolve a class in UCS Manager
        :param classId: The class ID to resolve (e.g., "orgOrg", "lsServer")
        :return: Parsed XML response
        """
        body = f'<configResolveClass cookie="{self.cookie}" classId="{classId}" inHierarchical="false"/>'
        root = self._send_request(body)

        # Pretty print the XML response
        console.print(f"Resolved Class XML for [blue]{classId}:[/]")
        xml_str = ET.tostring(root, encoding="unicode")
        print_xml(xml_str)

        return root

    def config_configure_object(self, payload):
        """
        Configure an object in UCS Manager
        :param payload: The XML payload to configure
        :return: Parsed XML response
        """
        body = (f'<configConfMo cookie="{self.cookie}" inHierarchical="false"><inConfig>{payload}</inConfig'
                f'></configConfMo>')
        print(body)
        root = self._send_request(body)

        # Pretty print the XML response\
        console.print(f"Configured XML for [blue]{payload}:[/]")
        xml_str = ET.tostring(root, encoding="unicode")
        print_xml(xml_str)

        return root


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy UCS Service Profiles via Template")
    parser.add_argument('--template', required=True, help="Service Profile Template Name")
    parser.add_argument('--prefix', required=True, help="Service Profile name prefix")
    parser.add_argument('--target_dn', required=True, help="Server DN to associate with the Service Profile")
    args = parser.parse_args()

    ucs = UCS(UCS_HOST, UCS_USER, UCS_PASSWORD)

    # Login to UCS Manager
    ucs.login()

    # Resolve the class for Service Profiles, build a list of existing templates that are available for server
    # provisioning
    classId = "lsServer"
    root = ucs.config_resolve_class(classId)

    out_configs = root.find("outConfigs")
    templates = []
    for ls_server in out_configs:
        # Only include initial templates, not update templates
        if ls_server.attrib.get("type") == "initial-template":
            template_name = ls_server.attrib.get("name")
            templates.append(template_name)

    console.print(f"[blue]Found {len(templates)} Service Profile Templates:[/]")
    for template in templates:
        console.print(f"  - {template}")

    # Check if the specified template exists
    if args.template not in templates:
        console.print(f"[red]Template '{args.template}' not found![/]")
        ucs.logout()
        exit(1)

    # Create Service Profile from Template
    payload = f'<lsServer  dn="org-root/ls-{args.prefix}" name="{args.prefix}" srcTemplName="{args.template}"/>'
    root = ucs.config_configure_object(payload)

    # Associate the Service Profile with the target server
    payload = (
        f'<lsBinding dn="org-root/ls-{args.prefix}" '
        f'pnDn="{args.target_dn}" restrictMigration="no"/>'
    )
    root = ucs.config_configure_object(payload)

    # Logout
    ucs.logout()
