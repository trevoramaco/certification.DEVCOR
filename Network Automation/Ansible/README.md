# Ansible IOS XE Automation Lab

This lab demonstrates how to automate configuration and information gathering from Cisco IOS XE devices using **Ansible**. It covers:

Ansible Cisco IOS Docs: https://docs.ansible.com/ansible/latest/collections/cisco/ios/index.html

- CLI-based automation with `cisco.ios` modules
- RESTCONF and NETCONF automation using `uri` and data models
- Inventory and variable management using `inventory.yml`, `group_vars`, and `host_vars`

## Prerequisites
1. Inventory: `inventory.yml`

```ini
[iosxe]
10.10.40.11

[iosxe:vars]
ansible_connection=ansible.netcommon.network_cli
ansible_user=admin
ansible_password=Admin!2345
ansible_become=yes
ansible_become_method=enable
ansible_network_os=cisco.ios.ios
ansible_command_timeout=60
```
2. Group Vars: `group_vars/iosxe.yaml`
```yaml
subnet_id: 60
```
3. Host Vars: `host_vars/10.10.40.11.yml`
```yaml
url: "https://{{ ansible_host }}/restconf"
ansible_user: "admin"
ansible_password: "Admin!2345"
```

## Sample Playbooks

To run all these playbooks:
```bash
ansible-playbook -i inventory.yml <folder>/<playbook>.yaml
```

### Loopback Automation
1. CLI-based Loopback
- File: `create_loopback.yaml`

```yaml
- name: Create Loopback interfaces
  hosts: iosxe
  gather_facts: no
  tasks:
    - name: Configure interfaces
      cisco.ios.ios_interfaces:
        config:
          - name: "{{subnet_id}}{{item}}"
            description: Ansible interface {{subnet_id}}{{item}}
            enabled: true
      loop:
        - 11
        - 12
        - 13
        - 14
```

2. RESTCONF-based Loopback

- File: `create_loopback.yml`

```yaml
- name: "Create Loopback via RESTCONF"
  hosts: iosxe
  connection: local
  tasks:
    - name: "TASK 1: Configure Loopback via RESTCONF"
      uri:
        url: "{{ url }}/data/Cisco-IOS-XE-native:native/interface/Loopback=100"
        user: "{{ ansible_user }}"
        password: "{{ ansible_password }}"
        method: PUT
        headers:
          Content-Type: 'application/yang-data+json'
          Accept:
            application/yang-data+json,
            application/yang-data.errors+json
        body_format: json
        body: "{{ loop_back_config }}"
        validate_certs: false
        status_code:
         - 200
         - 204
```

### NTP Configuration

1. Create NTP Server Configuration

- File: `create_ntp.yaml`

```yaml
- name: Set NTP servers
  hosts: iosxe
  gather_facts: no
  tasks:
    - name: Set NTP via CLI
      cisco.ios.ios_config:
        lines:
          - ntp server 10.1.{{subnet_id}}.{{item}}
      loop:
        - 11
        - 12
        - 13
        - 14
```

#### Show NTP (and ACL)

- Files: `show_ntp.yaml`, `show_ntp_acl.yaml`


### CLI Show and Facts Gathering

- `ios_show_commands.yaml`: Runs `show ip interface brief` and `show users`
- `int-facts.yaml`: Interface facts collection
- `ios_facts.yaml`: Gathers full device facts using `ios_facts`

### Cleanup

- File: `lab-cleanup.yaml`

Resets loopbacks and other test configurations created during the lab.

## Tips & Notes

- RESTCONF requires:
  ```bash
  conf t
  ip http secure-server
  restconf
  ```

- NETCONF requires:
  ```bash
  conf t
  netconf-yang
  ```

- CLI automation requires:
  - `ansible_connection=ansible.netcommon.network_cli`
  - Password prompt workaround: set `look_for_keys = False` in `ansible.cfg`

- RESTCONF automation uses `uri` with `connection: local` and does not require `ansible_network_os`


