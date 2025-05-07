import os
from intersight import ApiClient, Configuration, signing, ApiException
from intersight.api import compute_api, ntp_api, firmware_api
from intersight.model.mo_mo_ref import MoMoRef
from intersight.api.organization_api import OrganizationApi
from intersight.model.ntp_policy import NtpPolicy

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

# Rich console
console = Console()

# Load in Env variables
load_dotenv()

INTERSIGHT_KEY_ID = os.getenv("INTERSIGHT_KEY_ID")
INTERSIGHT_SECRET_FILE = os.getenv("INTERSIGHT_SECRET_FILE")


def _select_ntp_server_ips(ntp_servers: list) -> list:
    """
    Select NTP server IPs from a list of available NTP servers.
    :param ntp_servers: List of NTP servers
    :return: List of selected NTP server IPs
    """
    table = Table(title="Available NTP Servers")
    table.add_column("Index", justify="right", style="cyan")
    table.add_column("Server IP", style="green")

    ips = []
    for idx, server in enumerate(ntp_servers):
        ip = server.get("server_ip_address")
        if ip:
            table.add_row(str(idx), ip)
            ips.append(ip)

    console.print(table)

    # Select NTP servers, extract the IPs and combine into a list
    selection = Prompt.ask("Select server(s) by index", default="0")
    selected_indices = [int(i.strip()) for i in selection.split(",") if i.strip().isdigit()]
    selected_ips = [ips[i] for i in selected_indices if i < len(ips)]
    return selected_ips


def _select_organization(intersight_client):
    """
    Select an organization from the list of available organizations.
    :param intersight_client: Intersight API client
    :return: Selected organization object
    """
    org_api = OrganizationApi(intersight_client)
    orgs = org_api.get_organization_organization_list().results

    table = Table(title="Available Organizations")
    table.add_column("Index", justify="right", style="cyan")
    table.add_column("Name", style="green")

    for idx, org in enumerate(orgs):
        table.add_row(str(idx), org.name)

    console.print(table)

    # Select organization by index
    selection = Prompt.ask("Select org by index", default="0")
    selected_index = int(selection)
    selected_org = orgs[selected_index]

    # Create MoMoRef object for the selected organization
    return MoMoRef(
        class_id="mo.MoRef",
        object_type="organization.Organization",
        moid=selected_org.moid
    )


def get_intersight_client(api_key_id, private_key_path, endpoint="https://intersight.com"):
    """
    Create an Intersight API client with the provided API key and private key.
    :param api_key_id: API key ID
    :param private_key_path: Path to the private key file
    :param endpoint: Base URL for Intersight API
    :return: Intersight API client
    """
    # Load the private key
    with open(private_key_path, 'r') as f:
        private_key = f.read()

    if "BEGIN RSA PRIVATE KEY" in private_key:
        signing_algorithm = signing.ALGORITHM_RSASSA_PKCS1v15
    elif "BEGIN EC PRIVATE KEY" in private_key:
        signing_algorithm = signing.ALGORITHM_ECDSA_MODE_DETERMINISTIC_RFC6979
    else:
        raise ValueError("Unsupported private key format.")

    # Comes directly from SDK docs
    config = Configuration(
        host=endpoint,
        signing_info=signing.HttpSigningConfiguration(
            key_id=api_key_id,
            private_key_string=private_key,
            signing_scheme=signing.SCHEME_HS2019,
            signing_algorithm=signing_algorithm,
            hash_algorithm=signing.HASH_SHA256,
            signed_headers=[
                signing.HEADER_REQUEST_TARGET,
                signing.HEADER_HOST,
                signing.HEADER_DATE,
                signing.HEADER_DIGEST
            ]
        )
    )
    return ApiClient(config)


def get_compute_physical_summaries(intersight_client):
    """
    Get compute physical summaries from Intersight
    :param intersight_client: Intersight API client
    :return: List of compute physical summaries
    """
    compute_api_instance = compute_api.ComputeApi(intersight_client)
    try:
        response = compute_api_instance.get_compute_physical_summary_list()
        console.print(response)
        return response
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        return None


def get_ntp_policies(intersight_client):
    """
    Get NTP policies from Intersight
    :param intersight_client: Intersight API client
    :return: List of NTP policies
    """
    ntp_api_instance = ntp_api.NtpApi(intersight_client)
    try:
        response = ntp_api_instance.get_ntp_policy_list()
        console.print(response)
        return response
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        return None


def create_ntp_policy(intersight_client):
    """
    Create an NTP policy with existing servers
    :param intersight_client: Intersight API client
    :return: Response from the API
    """
    # Select organization first (multi-org requires context of which org to use)
    organization = _select_organization(intersight_client)

    # NTP API Instance, pick ntp servers
    ntp_api_instance = ntp_api.NtpApi(intersight_client)
    ntp_servers = ntp_api_instance.get_ntp_ntp_server_list()['results']
    ntp_ips = _select_ntp_server_ips([s.to_dict() for s in ntp_servers])

    # Build policy object
    ntp_policy = NtpPolicy(
        name="NTP-Policy-Example",
        enabled=True,
        ntp_servers=ntp_ips,
        organization=organization,
    )

    try:
        response = ntp_api_instance.create_ntp_policy(ntp_policy)
        console.print(response)
        return response
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        return None


def list_rack_servers_filtered(client):
    """
    List rack servers filtered by model
    :param client: Intersight API client
    """
    compute_api_instance = compute_api.ComputeApi(client)

    try:
        # Step 1: Retrieve distinct models (client-side only for discovery)
        all_racks = compute_api_instance.get_compute_rack_unit_list(top=1000).results
        models = sorted(set(r.model for r in all_racks if r.model))

        # Step 2: Prompt user for selection
        table = Table(title="Available Rack Server Models")
        table.add_column("Index", justify="right", style="cyan")
        table.add_column("Model", style="green")

        for idx, model in enumerate(models):
            table.add_row(str(idx), model)

        console.print(table)

        selection = Prompt.ask("Select model by index", choices=[str(i) for i in range(len(models))])
        selected_model = models[int(selection)]

        # Step 3: Use $filter to get servers with that model
        filter_str = f"Model eq '{selected_model}'"
        filtered_racks = compute_api_instance.get_compute_rack_unit_list(filter=filter_str).results

        # Step 4: Display results
        result_table = Table(title=f"Rack Servers (Filtered): {selected_model}")
        result_table.add_column("Name", style="bold cyan")
        result_table.add_column("Serial")
        result_table.add_column("Moid")

        for r in filtered_racks:
            result_table.add_row(
                r.name or "N/A",
                r.serial or "N/A",
                r.moid
            )

        console.print(result_table)

    except ApiException as e:
        console.print(f"[red]API Error:[/] {e}")


# === Exercise Menu ===
exercises = {
    "1": ("Get Compute Physical Summaries", get_compute_physical_summaries),
    "2": ("Get NTP Policies", get_ntp_policies),
    "3": ("Create NTP Policy with Existing Servers", create_ntp_policy),
    "4": ("List Rack Servers after Apply Filters", list_rack_servers_filtered),
}


def main_menu(intersight_client):
    """
    Main menu for selecting exercises to run.
    :param intersight_client: Intersight API client
    """
    console.print("\n[bold green]Select an Exercise to Run:[/bold green]")
    for key, (desc, _) in exercises.items():
        console.print(f"[cyan]{key}.[/] {desc}")

    choice = Prompt.ask("\nEnter your choice", choices=list(exercises.keys()), default="1", show_choices=False)
    _, func = exercises[choice]
    func(intersight_client)


if __name__ == "__main__":
    # Authenticate with Intersight
    intersight_client = get_intersight_client(INTERSIGHT_KEY_ID, INTERSIGHT_SECRET_FILE)
    console.print("[bold green]Intersight Client Initialized Successfully![/bold green] Successfully authenticated.")

    try:
        # Run the main menu
        main_menu(intersight_client)
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
