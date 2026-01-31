# ALPACA Group Module

## Overview

The `pcg.alpaca_operator.alpaca_group` module allows you to create, rename, or delete [ALPACA Operator](https://alpaca.pcg.io/) groups using the REST API. This module provides basic group management capabilities for organizing systems within the ALPACA Operator environment.

## Module Information

- **Module Name**: `pcg.alpaca_operator.alpaca_group`
- **Short Description**: Manage ALPACA Operator groups via REST API
- **Version Added**: 1.0.0
- **Requirements**:
  - Python >= 3.8
  - ansible-core >= 2.12
  - ALPACA Operator >= 5.6.0

## Parameters

### Required Parameters

| Parameter        | Type | Required | Description                                              |
| ---------------- | ---- | -------- | -------------------------------------------------------- |
| `name`           | str  | Yes      | Name of the group                                        |
| `api_connection` | dict | Yes      | Connection details for accessing the ALPACA Operator API |

### Optional Parameters

| Parameter  | Type | Required | Default | Description                                                                                                                                                                            |
| ---------- | ---- | -------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `new_name` | str  | No       | -       | Optional new name for the group. If the group specified in `name` exists, it will be renamed to this value. If the group does not exist, a new group will be created using this value. |
| `state`    | str  | No       | present | Desired state of the group (present, absent)                                                                                                                                           |

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

### Create a Group

```yaml
- name: Ensure group exists
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
    - name: Create group
      pcg.alpaca_operator.alpaca_group:
        name: testgroup01
        state: present
        api_connection: "{{ api_connection }}"
```

### Delete a Group

```yaml
- name: Ensure group is absent
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
    - name: Delete group
      pcg.alpaca_operator.alpaca_group:
        name: testgroup01
        state: absent
        api_connection: "{{ api_connection }}"
```

### Rename a Group

```yaml
- name: Rename an existing group
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
    - name: Rename group
      pcg.alpaca_operator.alpaca_group:
        name: testgroup01
        new_name: testgroup_renamed
        state: present
        api_connection: "{{ api_connection }}"
```

## Return Values

| Parameter | Type | Returned                                         | Description                                         |
| --------- | ---- | ------------------------------------------------ | --------------------------------------------------- |
| `changed` | bool | always                                           | Indicates whether any change was made to the group  |
| `msg`     | str  | always                                           | Human-readable message describing the outcome       |
| `id`      | int  | when state is present or absent and group exists | Numeric ID of the group (if known or newly created) |
| `name`    | str  | always                                           | Name of the group (new or existing)                 |

### Return Value Examples

#### Successful Group Creation

```json
{
  "changed": true,
  "msg": "Group created",
  "id": 42,
  "name": "testgroup01"
}
```

#### Group Already Exists

```json
{
  "changed": false,
  "msg": "Group already exists",
  "id": 42,
  "name": "testgroup01"
}
```

#### Group Renamed

```json
{
  "changed": true,
  "msg": "Group renamed",
  "id": 42,
  "name": "testgroup_renamed"
}
```

#### Group Deleted

```json
{
  "changed": true,
  "msg": "Group deleted",
  "name": "testgroup01"
}
```

## Notes

- The module supports check mode for previewing changes without applying them
- Group names must be unique within the ALPACA Operator environment
- When renaming a group, the new name must not conflict with existing group names
- The module will create a new group if the specified name doesn't exist and `new_name` is provided
- Groups can be used to organize systems within the ALPACA Operator environment
- The module uses token-based authentication for API communication
- API connection variables should be stored in the inventory file and referenced via `api_connection: "{{ api_connection }}"` in playbooks

## Author

- Jan-Karsten Hansmeyer (@pcg)