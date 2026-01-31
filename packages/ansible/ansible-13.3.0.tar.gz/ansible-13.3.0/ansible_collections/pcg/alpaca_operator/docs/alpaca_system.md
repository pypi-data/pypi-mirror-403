# ALPACA System Module

## Overview

The `pcg.alpaca_operator.alpaca_system` module allows you to create, update, or delete [ALPACA Operator](https://alpaca.pcg.io/) systems using the REST API. In addition to general system properties, it supports assigning agents and variables. Communication is handled using token-based authentication.

## Module Information

- **Module Name**: `pcg.alpaca_operator.alpaca_system`
- **Short Description**: Manage ALPACA Operator systems via REST API
- **Version Added**: 1.0.0
- **Requirements**:
  - Python >= 3.8
  - ansible-core >= 2.12
  - ALPACA Operator >= 5.6.0

## Parameters

### Required Parameters

| Parameter        | Type | Required | Description                                              |
| ---------------- | ---- | -------- | -------------------------------------------------------- |
| `name`           | str  | Yes      | Unique name (hostname) of the system                     |
| `api_connection` | dict | Yes      | Connection details for accessing the ALPACA Operator API |

### Optional Parameters

| Parameter         | Type | Required | Default | Description                                                                                                                                                                                                                                                               |
| ----------------- | ---- | -------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `new_name`        | str  | No       | -       | Optional new name for the system. If the system specified in `name` exists, it will be renamed to this value. If the system does not exist, a new system will be created using this value.                                                                                |
| `description`     | str  | No       | -       | Description of the system                                                                                                                                                                                                                                                 |
| `magic_number`    | int  | No       | -       | Custom numeric field between 0 and 59. Can be used for arbitrary logic in your setup                                                                                                                                                                                      |
| `checks_disabled` | bool | No       | -       | Disable automatic system health checks                                                                                                                                                                                                                                    |
| `group_name`      | str  | No       | -       | Name of the group to which the system should belong                                                                                                                                                                                                                       |
| `group_id`        | int  | No       | -       | ID of the group (used if `group_name` is not provided)                                                                                                                                                                                                                    |
| `rfc_connection`  | dict | No       | -       | Connection details for RFC communication                                                                                                                                                                                                                                  |
| `agents`          | list | No       | -       | A list of agents to assign to the system                                                                                                                                                                                                                                  |
| `variables`       | list | No       | -       | A list of variables to assign to the system                                                                                                                                                                                                                               |
| `variables_mode`  | str  | No       | update  | Controls how variables are handled when updating the system (update, replace). The value `update` adds missing variables and updates existing ones. The value `replace` adds missing variables, updates existing ones, and removes variables not defined in the playbook. |
| `state`           | str  | No       | present | Desired state of the system (present, absent)                                                                                                                                                                                                                             |

### Magic Number Choices

The `magic_number` parameter accepts values from 0 to 59.

### RFC Connection Configuration

The `rfc_connection` parameter accepts a dictionary with the following sub-options:

| Parameter           | Type | Required | Description                                            |
| ------------------- | ---- | -------- | ------------------------------------------------------ |
| `type`              | str  | No       | Type of RFC connection (none, instance, messageServer) |
| `host`              | str  | No       | Hostname or IP address of the RFC target system        |
| `instance_number`   | int  | No       | Instance number of the RFC connection (0-99)           |
| `sid`               | str  | No       | SAP system ID (SID), consisting of 3 uppercase letters |
| `logon_group`       | str  | No       | Logon group (used with message server type)            |
| `username`          | str  | No       | Username for RFC connection                            |
| `password`          | str  | No       | Password for the RFC connection                        |
| `client`            | str  | No       | Client for RFC connection                              |
| `sap_router_string` | str  | No       | SAProuter string used to establish the RFC connection  |
| `snc_enabled`       | bool | No       | Enable or disable SNC                                  |

**Type Choices**: none, instance, messageServer

**Instance Number Choices**: 0-99

#### ⚠️ Important Note About RFC Password

**IMPORTANT**: If you specify the `password` parameter in the `rfc_connection` block in your playbook, the module will **ALWAYS** report a change (`changed=true`) on every playbook run, even if nothing has actually changed.

**Why does this happen?**
- The ALPACA Operator API does not return the current RFC password for security reasons
- The module cannot compare the desired password with the current password
- Therefore, it cannot determine if the password actually needs to be updated
- This breaks the idempotency of the module

**Best Practice:**
1. **Initial Setup**: Include the password when creating the system for the first time
2. **After Setup**: Comment out or remove the `password` parameter from your playbook
3. **Password Changes**: Only uncomment the password when you actually need to change it
```

This approach maintains idempotency while still allowing you to manage RFC passwords when needed.

### Agent Assignment

The `agents` parameter accepts a list of dictionaries, where each dictionary must include:

| Parameter | Type | Required | Description       |
| --------- | ---- | -------- | ----------------- |
| `name`    | str  | Yes      | Name of the agent |

### Variable Assignment

The `variables` parameter accepts a list of dictionaries, where each dictionary must include:

| Parameter | Type | Required | Description                     |
| --------- | ---- | -------- | ------------------------------- |
| `name`    | str  | Yes      | Name of the variable            |
| `value`   | raw  | Yes      | Value to assign to the variable |

### API Connection Configuration

The `api_connection` parameter requires a dictionary with the following sub-options:

| Parameter    | Type | Required | Default   | Description                                                 |
| ------------ | ---- | -------- | --------- | ----------------------------------------------------------- |
| `username`   | str  | Yes      | -         | Username for authentication against the ALPACA Operator API |
| `password`   | str  | Yes      | -         | Password for authentication against the ALPACA Operator API |
| `protocol`   | str  | No       | https     | Protocol to use (http or https)                             |
| `host`       | str  | No       | localhost | Hostname of the ALPACA Operator server                      |
| `port`       | int  | No       | 8443      | Port of the ALPACA Operator API                             |
| `tls_verify` | bool | No       | true      | Validate SSL certificates                                   |

## Examples

### Create a System with Full Configuration

```yaml
- name: Ensure system exists
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
    - name: Create system
      pcg.alpaca_operator.alpaca_system:
        name: system01
        description: My Test System
        magic_number: 42
        checks_disabled: false
        group_name: test-group
        rfc_connection:
          type: instance
          host: test-host
          instance_number: 30
          sid: ABC
          logon_group: my-logon-group
          username: rfc_myUser
          password: rfc_myPasswd
          client: 123
          sap_router_string: rfc_SAPRouter
          snc_enabled: false
        agents:
          - name: localhost
          - name: testjan01-agent
        variables:
          - name: "<BKP_DATA_CLEANUP_INT>"
            value: "19"
          - name: "<BKP_DATA_CLEANUP_INT2>"
            value: "this is a string"
          - name: "<BKP_DATA_DEST2>"
            value: "11"
        state: present
        api_connection: "{{ api_connection }}"
```

### Delete a System

```yaml
- name: Ensure system is absent
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
    - name: Delete system
      pcg.alpaca_operator.alpaca_system:
        name: system01
        state: absent
        api_connection: "{{ api_connection }}"
```

### Rename a System

```yaml
- name: Rename an existing system
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
    - name: Rename system
      pcg.alpaca_operator.alpaca_system:
        name: system01
        new_name: system_renamed
        api_connection: "{{ api_connection }}"
```

### Create a System with RFC Connection Only

```yaml
- name: Create system with RFC connection
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
    - name: Create SAP system
      pcg.alpaca_operator.alpaca_system:
        name: sap-system-01
        description: SAP Production System
        rfc_connection:
          type: instance
          host: sap-prod-server
          instance_number: 00
          sid: PRD
          username: rfc_user
          password: rfc_password
          client: 100
        state: present
        api_connection: "{{ api_connection }}"
```

### Create a System with Variables Only

```yaml
- name: Create system with variables
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
    - name: Create configuration system
      pcg.alpaca_operator.alpaca_system:
        name: config-system-01
        description: Configuration System
        variables:
          - name: "BACKUP_PATH"
            value: "/backup/data"
          - name: "RETENTION_DAYS"
            value: "30"
          - name: "ENVIRONMENT"
            value: "production"
        state: present
        api_connection: "{{ api_connection }}"
```

## Return Values

| Parameter | Type | Returned              | Description                           |
| --------- | ---- | --------------------- | ------------------------------------- |
| `system`  | dict | when state is present | System details                        |
| `msg`     | str  | always                | Status message describing the outcome |
| `changed` | bool | always                | Whether any changes were made         |

### Return Value Examples

#### Successful System Creation

```json
{
  "system": {
    "id": 42,
    "name": "system01",
    "description": "My Test System",
    "magic_number": 42,
    "checks_disabled": false,
    "group_name": "test-group",
    "rfc_connection": {
      "type": "instance",
      "host": "test-host",
      "instance_number": 30,
      "sid": "ABC"
    },
    "agents": [
      {"name": "localhost"},
      {"name": "testjan01-agent"}
    ],
    "variables": [
      {"name": "<BKP_DATA_CLEANUP_INT>", "value": "19"},
      {"name": "<BKP_DATA_CLEANUP_INT2>", "value": "this is a string"}
    ]
  },
  "msg": "System created successfully",
  "changed": true
}
```

## Notes

- The module supports check mode for previewing changes without applying them
- System names must be unique within the ALPACA Operator environment
- When renaming a system, the new name must not conflict with existing system names
- The `magic_number` field can be used for custom logic in your setup
- RFC connections support both instance and message server types
- Agent assignments and variable assignments are optional
- The currently configured RFC password cannot be retrieved or compared via the API
- To ensure a new RFC password is applied, you must change at least one additional attribute
- Variables can be of any type (string, integer, boolean, etc.)
- The module uses token-based authentication for API communication
- API connection variables should be stored in the inventory file and referenced via `api_connection: "{{ api_connection }}"` in playbooks

## Author

- Jan-Karsten Hansmeyer (@pcg)