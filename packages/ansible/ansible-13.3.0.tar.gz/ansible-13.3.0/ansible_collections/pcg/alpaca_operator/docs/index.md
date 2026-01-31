# ALPACA Operator Ansible Collection Documentation

## Overview

The ALPACA Operator Ansible Collection provides a comprehensive set of modules for managing [ALPACA Operator](https://alpaca.pcg.io/) environments through Ansible automation. This collection enables you to manage agents, systems, groups, commands, and command sets using the ALPACA Operator REST API.

## Modules

### Core Management Modules

| Module                                                  | Description                    | Use Case                                                                              |
| ------------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------------------- |
| [`pcg.alpaca_operator.alpaca_agent`](alpaca_agent.md)   | Manage ALPACA Operator agents  | Create, update, delete, and configure agents with escalation settings                 |
| [`pcg.alpaca_operator.alpaca_system`](alpaca_system.md) | Manage ALPACA Operator systems | Create, update, delete systems with RFC connections, agent assignments, and variables |
| [`pcg.alpaca_operator.alpaca_group`](alpaca_group.md)   | Manage ALPACA Operator groups  | Create, rename, and delete groups for organizing systems                              |

### Command Management Modules

| Module                                                            | Description                                | Use Case                                                 |
| ----------------------------------------------------------------- | ------------------------------------------ | -------------------------------------------------------- |
| [`pcg.alpaca_operator.alpaca_command`](alpaca_command.md)         | Manage individual ALPACA Operator commands | Fine-grained control over single command properties      |
| [`pcg.alpaca_operator.alpaca_command_set`](alpaca_command_set.md) | Manage command sets for systems            | Bulk management of all commands associated with a system |

## Installation

### Prerequisites

- SLES 15 SP4 or later (or compatible Linux distribution)
- Python >= 3.8
- ansible-core >= 2.12
- ALPACA Operator >= 5.6.0
- Root or sudo access for system-level installation
- Internet connectivity for package installation

### Step 1: Check Python Version

First, determine your Python version to select the appropriate Ansible version:

```bash
ls /usr/bin/python*
python3 --version
```

Refer to the [Support Matrix](../README.md#support-matrix) in the main README to determine which Ansible version is compatible with your Python version.

### Step 2: Install Ansible

#### Option A: Install via Zypper (Recommended for SLES)

```bash
# Add the Ansible repository
sudo zypper addrepo https://download.opensuse.org/repositories/systemsmanagement:/ansible/SLE_15_SP4/ ansible

# Refresh repositories
sudo zypper refresh

# Install Ansible (replace X.Y with your chosen version, e.g., 2.17)
sudo zypper install ansible-2.17
```

#### Option B: Install via pip

```bash
# Install pip if not available
sudo zypper install python3-pip

# Install specific Ansible version (replace X.Y.Z with your chosen version)
pip3 install ansible==2.17.0
```

#### Verify Installation

```bash
ansible --version
```

### Step 3: Install ALPACA Operator Collection

#### Option A: Install from Ansible Galaxy (Recommended)

```bash
ansible-galaxy collection install pcg.alpaca_operator
```

#### Option B: Install from Git Repository

```bash
ansible-galaxy collection install git+https://github.com/pcg-sap/alpaca-operator-ansible.git
```

#### Option C: Manual Installation from Release

1. Download the latest release from [GitHub Releases](https://github.com/pcg-sap/alpaca-operator-ansible/releases)
2. Copy the release archive to your server
3. Extract the archive
4. Change to the extracted directory
5. Install the collection:

```bash
# Navigate to the extracted directory
cd alpaca-operator-ansible-*

# Install the collection (optional use --force to overwrite existing installation)
ansible-galaxy collection install ./ --force

# Verify collection was installed
ansible-galaxy collection list
```

**Note**: If you installed the collection manually, the path might be different. Adjust the path to where you extracted the collection.

## Getting Started

### Step 1: Create Project Directory

Create a working directory for your Ansible automation:

```bash
mkdir -p ~/alpaca-ansible-automation
cd ~/alpaca-ansible-automation
```

### Step 2: Configure Ansible

Create an Ansible configuration file:

```bash
cat > ansible.cfg << 'EOF'
[defaults]
inventory = ./inventory.ini
host_key_checking = False
EOF
```

### Step 3: Create Inventory

Create an inventory file with your ALPACA API configuration:

```bash
cat > inventory.ini << 'EOF'
[local]
localhost ansible_connection=local

[local:vars]
ansible_python_interpreter=/usr/bin/python3

# ALPACA API Configuration
ALPACA_Operator_API_Host='localhost'
ALPACA_Operator_API_Protocol='https'
ALPACA_Operator_API_Port='8443'
ALPACA_Operator_API_Username='<username>'
ALPACA_Operator_API_Password='<password>'
ALPACA_Operator_API_Validate_Certs=False
EOF
```

**Important Notes:**
- Customize API username and password according to your environment
- If you have multiple Python versions installed, specify the exact interpreter path
- Available Python versions can be checked with: `ls /usr/bin/python*`
- Avoid using generic `python3` if multiple Python 3.x versions are installed

**Python interpreter examples:**
- `/usr/bin/python3.9` - Python 3.9
- `/usr/bin/python3.10` - Python 3.10
- `/usr/bin/python3.11` - Python 3.11
- `/usr/bin/python3.12` - Python 3.12

### Step 4: Test ALPACA API Connection

Create and run a test playbook to verify API connectivity:

```bash
mkdir playbooks
cat > playbooks/test_connection.yml << 'EOF'
---
- name: Test ALPACA API Connection
  hosts: local
  gather_facts: false

  tasks:
    - name: Test API connection using ALPACA module utilities
      block:
        - name: Import ALPACA API utilities
          ansible.builtin.set_fact:
            api_url: "{{ ALPACA_Operator_API_Protocol }}://{{ ALPACA_Operator_API_Host }}:{{ ALPACA_Operator_API_Port }}/api"

        - name: Test authentication and API access
          ansible.builtin.uri:
            url: "{{ api_url }}/auth/login"
            method: POST
            body_format: json
            body: '{"username": "{{ ALPACA_Operator_API_Username }}", "password": "{{ ALPACA_Operator_API_Password }}"}'
            validate_certs: "{{ ALPACA_Operator_API_Validate_Certs }}"
            status_code: [200, 401, 403]
          register: auth_test

        - name: Display authentication result
          ansible.builtin.debug:
            msg: "Authentication test: {{ 'SUCCESS' if auth_test.status == 200 else 'FAILED' }} (Status: {{ auth_test.status }})"

        - name: Show API token (if authentication successful)
          ansible.builtin.debug:
            msg: "API Token obtained: {{ auth_test.json.token | default('None') | truncate(20, true, '...') }}"
          when: auth_test.status == 200

      rescue:
        - name: Display connection error
          ansible.builtin.debug:
            msg: "Connection failed: {{ ansible_failed_result.msg | default('Unknown error') }}"
          failed_when: true

EOF

# Run the test
ansible-playbook playbooks/test_connection.yml
```

### Step 5: Create Your First Playbook

Create a basic playbook to manage your ALPACA environment:

```yaml
# playbooks/manage_environment.yml
---
- name: Manage ALPACA Operator Environment
  hosts: local
  gather_facts: false

  vars:
    api_connection:
      host: "{{ ALPACA_Operator_API_Host }}"
      protocol: "{{ ALPACA_Operator_API_Protocol }}"
      port: "{{ ALPACA_Operator_API_Port }}"
      username: "{{ ALPACA_Operator_API_Username }}"
      password: "{{ ALPACA_Operator_API_Password }}"
      tls_verify: "{{ ALPACA_Operator_API_Validate_Certs }}"

  tasks:
    - name: Create a group
      pcg.alpaca_operator.alpaca_group:
        name: production
        state: present
        api_connection: "{{ api_connection }}"

    - name: Create an agent
      pcg.alpaca_operator.alpaca_agent:
        name: backup-agent-01
        description: Backup Agent for Production
        ip_address: 192.168.1.100
        location: virtual
        state: present
        api_connection: "{{ api_connection }}"
```

### Step 6: Run Your Playbook

Execute the playbook:

```bash
# Run in check mode first (dry run) with verbosity
ansible-playbook playbooks/manage_environment.yml --check -v

# Execute the playbook for real deployment
ansible-playbook playbooks/manage_environment.yml
```

## Best Practices

### 1. Use Variables for API Connection

Store your API connection details in the inventory file:

```ini
# inventories/alpaca.ini
[local]
localhost ansible_connection=local ansible_python_interpreter=python3

[local:vars]
ALPACA_Operator_API_Host='your-alpaca-server'
ALPACA_Operator_API_Protocol='https'
ALPACA_Operator_API_Port='8443'
ALPACA_Operator_API_Username='your-username'
ALPACA_Operator_API_Password='your-password'
ALPACA_Operator_API_Validate_Certs=False
```

Then reference them in your playbook:

```yaml
vars:
  api_connection:
    host: "{{ ALPACA_Operator_API_Host }}"
    protocol: "{{ ALPACA_Operator_API_Protocol }}"
    port: "{{ ALPACA_Operator_API_Port }}"
    username: "{{ ALPACA_Operator_API_Username }}"
    password: "{{ ALPACA_Operator_API_Password }}"
    tls_verify: "{{ ALPACA_Operator_API_Validate_Certs }}"
```

### 2. Use Check Mode for Testing

Always test your playbooks in check mode first:

```bash
ansible-playbook your-playbook.yml --check
```

### 3. Organize by Environment

Structure your playbooks to separate different environments:

```
playbooks/
├── production/
│   ├── agents.yml
│   ├── systems.yml
│   └── commands.yml
├── staging/
│   ├── agents.yml
│   ├── systems.yml
│   └── commands.yml
└── common/
    └── groups.yml
```

### 4. Enable Verbose Output for Debugging

Use different levels of verbosity when debugging issues:

```bash
ansible-playbook your-playbook.yml -v    # Basic verbose
ansible-playbook your-playbook.yml -vv   # More verbose
ansible-playbook your-playbook.yml -vvv  # Very verbose (debug level)
```

### Getting Help

If you encounter issues not covered in this troubleshooting guide:

1. Check the [GitHub Issues](https://github.com/pcg-sap/alpaca-operator-ansible/issues) for similar problems
2. Review module-specific documentation in the [docs](.) directory
3. Enable verbose output (`-vvv`) to get detailed error information
4. Create a new issue with:
   - Ansible version (`ansible --version`)
   - Collection version (`ansible-galaxy collection list pcg.alpaca_operator`)
   - Python version (`python3 --version`)
   - Error message and stack trace
   - Minimal reproducible example

## Support

For issues and questions:

- **GitHub Issues**: [https://github.com/pcg-sap/alpaca-operator-ansible/issues](https://github.com/pcg-sap/alpaca-operator-ansible/issues)
- **Author**: Jan-Karsten Hansmeyer (@pcg)

## License

Apache License, Version 2.0
