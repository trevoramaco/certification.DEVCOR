import os

import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from ucsmsdk.ucshandle import UcsHandle
from ucsmsdk.mometa.fabric.FabricVlan import FabricVlan

# Rich console
console = Console()

# Load in Env variables
load_dotenv()

UCS_HOST = os.getenv("UCS_HOST")
UCS_USER = os.getenv("UCS_USER")
UCS_PASSWORD = os.getenv("UCS_PASSWORD")

# Disable warnings for insecure HTTPS requests
requests.packages.urllib3.disable_warnings()

# Connect and log in to UCS Manager
handle = UcsHandle(UCS_HOST, UCS_USER, UCS_PASSWORD)
handle.login()


def exercise_1_query_blades():
    """Query and display all compute blades"""
    blades = handle.query_classid("computeBlade")
    console.print("\n[blue]Compute Blades:[/]")
    for blade in blades:
        # Access attribute fields of each blade
        console.print(f"Blade: {blade.dn}, CPUs: {blade.num_of_cpus}, Memory: {blade.available_memory}")


def exercise_2_query_and_modify_leds():
    """Query and modify LEDs on compute resources"""
    compute_resources = handle.query_classids("ComputeBlade", "ComputeRackUnit")

    console.print("\n[blue]Compute Resources and their LEDs:[/]")
    # Iterate through blades and chassis servers
    for compute_resource_class in compute_resources:
        for compute_resource in compute_resources[compute_resource_class]:
            # Query children of the compute resource (in this example: LED Locator)
            leds = handle.query_children(in_dn=compute_resource.dn, class_id="equipmentLocatorLed")
            console.print(f"Resource: {compute_resource.dn}, Current LED States: {[led.oper_state for led in leds]}")

            if leds[0].oper_state == "on":
                leds[0].admin_state = "off"
            else:
                leds[0].admin_state = "on"

            handle.set_mo(leds[0])
            handle.commit()

            # Re-query the LED state to confirm the change
            console.print(f"Updated LED State: {leds[0].admin_state}")


def exercise_3_create_vlans():
    """Create VLANs in UCS Manager"""
    lan_cloud = handle.query_classid("FabricLanCloud")

    if not lan_cloud:
        console.print("[red]No LAN Cloud found![/]")
        return

    # Create VLANs
    vlans = ["200", "201", "202"]

    console.print(f"Creating VLANs: {vlans} in LAN Cloud: {lan_cloud[0].dn}")
    for vlan in vlans:
        vlan_mo = FabricVlan(parent_mo_or_dn=lan_cloud[0], name="vlan" + vlan, id=vlan)
        handle.add_mo(vlan_mo, True)

    handle.commit()
    console.print(f"[green]VLANs {vlans} created successfully![/]")


def exercise_4_list_vlans():
    """List all VLANs configured in UCS Manager"""
    console.print("\n[blue]Listing VLANs in UCS Manager:[/]")
    vlans = handle.query_classid("FabricVlan")

    if not vlans:
        console.print("[yellow]No VLANs found.[/]")
        return

    for vlan in vlans:
        console.print(f"VLAN: {vlan.name}, ID: {vlan.id}, Status: {vlan.status}, DN: {vlan.dn}")


def exercise_5_delete_vlans():
    """Delete VLANs in UCS Manager"""
    console.print("\n[blue]Deleting VLANs in UCS Manager:[/]")
    vlans = handle.query_classid("FabricVlan")

    if not vlans:
        console.print("[yellow]No VLANs found.[/]")
        return

    # Delete VLANs except for VLAN 1
    for vlan_mo in vlans:
        console.print(f"Deleting VLAN: {vlan_mo.name}, ID: {vlan_mo.id}, DN: {vlan_mo.dn}")
        if vlan_mo.id != "1":
            handle.remove_mo(vlan_mo)

    handle.commit()
    console.print("[green]VLANs deleted successfully![/]")

# === Exercise Menu ===
exercises = {
    "1": ("Query all compute blades", exercise_1_query_blades),
    "2": ("Query and modify LEDs on compute resources", exercise_2_query_and_modify_leds),
    "3": ("Create VLANs in UCS Manager", exercise_3_create_vlans),
    "4": ("List all VLANs configured in UCS Manager", exercise_4_list_vlans),
    "5": ("Delete VLANs in UCS Manager", exercise_5_delete_vlans),
    # Add more entries as needed
}


def main_menu():
    """
    Main menu to select exercises
    """
    console.print("\n[bold green]Select an Exercise to Run:[/bold green]")
    for key, (desc, _) in exercises.items():
        console.print(f"[cyan]{key}.[/] {desc}")

    choice = Prompt.ask("\nEnter your choice", choices=list(exercises.keys()), default="1")
    _, func = exercises[choice]
    func()


if __name__ == "__main__":
    try:
        main_menu()
    finally:
        handle.logout()
        console.print("\n[green]Logged out from UCS Manager[/]")
