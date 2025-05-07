# Cisco DEVCOR Personal Lab Repository

This repository contains hands-on labs and reference code for the **Cisco DevNet Professional (DEVCOR 350-901 v1.1)** exam. It contains various python examples covering the core Cisco platforms from the exam blueprint.

Exam Topics: https://learningnetwork.cisco.com/s/devcor-exam-topics

## Disclaimer
This repository is intended **solely for educational and demonstration purposes**. It is not affiliated with or endorsed by Cisco Systems. All opinions, designs, and scripts are created by the repository author.

**This repository is in no way "official" or "certified" by Cisco.** It is a personal project to help individuals prepare for the DEVCOR exam and gain hands-on experience with Cisco's APIs and platforms.

## Common Pre-requisites
- Python 3.8+
- Required Libraries: `pip install -r requirements.txt`
- `.env_sample`: Copy and rename to `.env` and plug in the various API keys and credentials for the labs (as detailed in their READMEs)

> Other specific pre-requisites are called out in the individual lab READMEs.

## Lab Environments
**These labs do not provide or call out environments to use**. 

> Personally I used a combination of:
> - A Homelab Cisco 3850 switch
> - Various VMs (like the FTDv VM) - deploy on my own VMWare ESXI Environment
> - A Linux server (Docker, Kubernetes, etc.)
> - Cisco Devnet Sandboxes
> - Cisco Devnet Learning Labs (and their Sandboxes)
> - Cisco dCloud Environments (requires a Cisco account)

Any working environment will do, and the labs assume the environment is set up and API access is available for the user (aka: an API key was generated, proper RBAC, etc.)
- [Cisco DevNet Learning Labs](https://developer.cisco.com/learning/)
- [Cisco DevNet Sandbox](https://devnetsandbox.cisco.com/)
- [Cisco dCloud](https://dcloud.cisco.com/)
- [Cisco Software Download](https://software.cisco.com/download/home)

## Lab Modules

### [Catalyst Center](./Catalyst%20Center/README.md)
- REST API with X-Auth-Token
- Command Runner, Inventory, Site Health, Topology
- Pagination, polling, and CLI interactivity

### [Docker](./Docker/README.md)
- Minimal Flask API with Single Endpoint
- Containerized using Docker

### [FDM (Firepower Device Manager)](./FDM/README.md)
- Authenticates to FDM
- Grabs Existing List of Network Objects
- Reads a CSV of network objects (`HOST`, `NETWORK`, `FQDN`, `RANGE`)
- Validates input and creates missing objects
- Deploys configuration and checks status

### [Intersight](./Intersight/README.md)
- List all physical compute summaries (rack servers)
- Create a new NTP Policy using interactive prompts 
- Filter physical rack servers using `$filter` (by model)

### [Kubernetes](./Kubernetes/README.md)
- Interact with Kubernetes `Minikube` cluster using the `kubernetes` Python client
- Create a simple voting app using `Flask` and `Redis`
- Deploy the app to the Kubernetes cluster

### [Meraki](./Meraki/README.md)
- Listens for POST requests from Meraki Scanning API
- Validates and processes incoming location data
- Tracks unique MAC addresses seen via WiFi or Bluetooth
- Displays a running terminal table with MAC address and last seen time

### [Ansible](./Network%20Automation/Ansible/README.md)
- CLI-based automation with `cisco.ios` modules
- RESTCONF and NETCONF automation using `uri` and data models
- Inventory and variable management using `inventory.yml`, `group_vars`, and `host_vars`

### [RESTCONF](./Network%20Automation/RESTCONF/README.md)
- Create a new Loopback interface on a Cisco IOS XE device via the RESTCONF API
- Use `requests` to interact with RESTCONF
- Structure YANG-based payloads using `ietf-interfaces`

### [Terraform](./Network%20Automation/Terraform/README.md)
- Enable and configure telemetry subscriptions on IOS XE
- Use Terraform to automate configuration deployment
- Practice init / plan / apply / destroy Terraform workflow

### [TIG-MDT Stack](./TIG-MDT/README.md)
- Interact with the **TIG** stack (Telegraf, InfluxDB, Grafana)
- Stream **CPU data** from a Cisco IOS XE device into **InfluxDB**, using **NETCONF-YANG with YANG Push** and visualize it with **Grafana**

### [UCS Manager](./UCS%20Manager/README.md)
- Raw XML API (MIT model)
- Service Profile template provisioning via API
- VLAN and compute blade interaction via SDK
