# ALPACA Agent Module

## Overview

The `pcg.alpaca_operator.alpaca_agent` module allows you to create, update, or delete [ALPACA Operator](https://alpaca.pcg.io/) agents using the REST API. This module provides comprehensive management capabilities for ALPACA Operator agents, including configuration of escalation settings, location settings, and other agent-specific properties.

## Module Information

- **Module Name**: `pcg.alpaca_operator.alpaca_agent`
- **Short Description**: Manage ALPACA Operator agents via REST API
- **Version Added**: 1.0.0
- **Requirements**:
  - Python >= 3.8
  - ansible-core >= 2.12
  - ALPACA Operator >= 5.6.0

## Parameters

### Required Parameters

| Parameter        | Type | Required | Description                                              |
| ---------------- | ---- | -------- | -------------------------------------------------------- |
| `name`           | str  | Yes      | Unique name (hostname) of the agent                      |
| `api_connection` | dict | Yes      | Connection details for accessing the ALPACA Operator API |

### Optional Parameters

| Parameter         | Type | Required | Default | Description                                                                                                                                                                            |
| ----------------- | ---- | -------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `new_name`        | str  | No       | -       | Optional new name for the agent. If the agent specified in `name` exists, it will be renamed to this value. If the agent does not exist, a new agent will be created using this value. |
| `description`     | str  | No       | -       | Unique description of the agent                                                                                                                                                        |
| `escalation`      | dict | No       | -       | Escalation configuration                                                                                                                                                               |
| `ip_address`      | str  | No       | -       | IP address of the agent                                                                                                                                                                |
| `location`        | str  | No       | virtual | Location of the agent (virtual, local1, local2, remote)                                                                                                                                |
| `script_group_id` | int  | No       | -1      | Script Group ID                                                                                                                                                                        |
| `state`           | str  | No       | present | Desired state of the agent (present, absent)                                                                                                                                           |

### Escalation Configuration

The `escalation` parameter accepts a dictionary with the following sub-options:

| Parameter                | Type | Required | Default | Description                          |
| ------------------------ | ---- | -------- | ------- | ------------------------------------ |
| `failures_before_report` | int  | No       | 0       | Number of failures before reporting  |
| `mail_enabled`           | bool | No       | false   | Whether mail notification is enabled |
| `mail_address`           | str  | No       | ""      | Mail address for notifications       |
| `sms_enabled`            | bool | No       | false   | Whether SMS notification is enabled  |
| `sms_address`            | str  | No       | ""      | SMS address for notifications        |

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

### Create an Agent

```yaml
- name: Ensure agent exists
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
    - name: Create agent
      pcg.alpaca_operator.alpaca_agent:
        name: agent01
        ip_address: 192.168.1.100
        location: virtual
        description: Test agent
        escalation:
          failures_before_report: 3
          mail_enabled: true
          mail_address: my.mail@pcg.io
          sms_enabled: true
          sms_address: 0123456789
        script_group_id: 0
        state: present
        api_connection: "{{ api_connection }}"
```

### Delete an Agent

```yaml
- name: Ensure agent is absent
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
    - name: Delete agent
      pcg.alpaca_operator.alpaca_agent:
        name: agent01
        state: absent
        api_connection: "{{ api_connection }}"
```

### Rename an Agent

```yaml
- name: Rename an existing agent
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
    - name: Rename agent
      pcg.alpaca_operator.alpaca_agent:
        name: agent01
        new_name: agent_renamed
        state: present
        api_connection: "{{ api_connection }}"
```

## Return Values

| Parameter      | Type | Returned                                    | Description                                                                  |
| -------------- | ---- | ------------------------------------------- | ---------------------------------------------------------------------------- |
| `msg`          | str  | always                                      | Status message indicating the result of the operation                        |
| `changed`      | bool | always                                      | Indicates whether any change was made                                        |
| `agent_config` | dict | when state is present or absent             | Details of the created, updated, or deleted agent configuration              |
| `changes`      | dict | when state is present and a change occurred | Dictionary showing differences between the current and desired configuration |

### Return Value Examples

#### Successful Agent Creation

```json
{
  "msg": "Agent created",
  "changed": true,
  "agent_config": {
    "id": 7,
    "hostname": "testagent",
    "description": "Test agent",
    "ip_address": "10.1.1.1",
    "location": "virtual",
    "script_group_id": 2,
    "escalation": {
      "failures_before_report": 3,
      "mail_enabled": true,
      "mail_address": "monitoring@pcg.io",
      "sms_enabled": false,
      "sms_address": ""
    }
  }
}
```

#### Agent Update with Changes

```json
{
  "msg": "Agent updated",
  "changed": true,
  "changes": {
    "ip_address": {
      "current": "10.1.1.1",
      "desired": "10.1.1.2"
    },
    "escalation": {
      "mail_enabled": {
        "current": false,
        "desired": true
      }
    }
  }
}
```

## Notes

- The module supports check mode for previewing changes without applying them
- Agent names must be unique within the ALPACA Operator environment
- When renaming an agent, the new name must not conflict with existing agent names
- Escalation settings are optional and can be configured independently
- The `script_group_id` parameter defaults to -1 if not specified
- Location options include: virtual, local1, local2, remote
- API connection variables should be stored in the inventory file and referenced via `api_connection: "{{ api_connection }}"` in playbooks

## Author

- Jan-Karsten Hansmeyer (@pcg)