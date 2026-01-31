# ALPACA Command Set Module

## Overview

The `pcg.alpaca_operator.alpaca_command_set` module manages an entire set of [ALPACA Operator](https://alpaca.pcg.io/) commands associated with a system using a REST API. It is designed to apply bulk changes, for example, deploying multiple commands at once or cleaning up an existing command set.

Use this module when you need to apply or remove multiple commands at once on a given ALPACA system. It simplifies large-scale system updates and is optimal for automation scenarios.

**Important**: This module takes full control of the command set on the target system. Any commands not defined via Ansible will be removed from the system!

## Module Information

- **Module Name**: `pcg.alpaca_operator.alpaca_command_set`
- **Short Description**: Manage all ALPACA Operator commands of a specific system via REST API
- **Version Added**: 1.0.0
- **Requirements**:
  - Python >= 3.8
  - ansible-core >= 2.12
  - ALPACA Operator >= 5.6.0

## Parameters

### Required Parameters

| Parameter       | Type | Required | Description                                                                                      |
| --------------- | ---- | -------- | ------------------------------------------------------------------------------------------------ |
| `system`        | dict | Yes      | Dictionary containing system identification. Either `system_id` or `system_name` must be provided. |
| `api_connection` | dict | Yes      | Connection details for accessing the ALPACA Operator API                                         |

### Optional Parameters

| Parameter  | Type | Required | Default | Description                        |
| ---------- | ---- | -------- | ------- | ---------------------------------- |
| `commands` | list | No       | []      | List of desired commands to manage |

### System Identification

The `system` parameter accepts a dictionary with the following sub-options:

| Parameter    | Type | Required | Description                                                            |
| ------------ | ---- | -------- | ---------------------------------------------------------------------- |
| `system_id`   | int  | No*      | Numeric ID of the target system. Optional if `system_name` is provided. |
| `system_name` | str  | No*      | Name of the target system. Optional if `system_id` is provided.         |

*Either `system_id` or `system_name` must be provided.

### Command Configuration

The `commands` parameter accepts a list of dictionaries, where each dictionary can include the following fields:

| Parameter          | Type | Required | Default | Description                                                                                |
| ------------------ | ---- | -------- | ------- | ------------------------------------------------------------------------------------------ |
| `name`             | str  | No       | -       | Name or description of the command                                                         |
| `state`            | str  | No       | present | Desired state of the command (present, absent)                                             |
| `agent_id`          | int  | No       | -       | Numeric ID of the agent. Optional if `agent_name` is provided.                              |
| `agent_name`        | str  | No       | -       | Name of the agent. Optional if `agent_id` is provided.                                      |
| `process_id`        | int  | No       | -       | ID of the process to be executed. Optional if `process_central_id` is provided.              |
| `process_central_id` | int  | No       | -       | Central ID / Global ID of the process to be executed. Optional if `process_id` is provided. |
| `parameters`       | str  | No       | -       | Parameters for the process                                                                 |
| `parameters_needed` | bool | No       | -       | Whether the execution of the command requires additional parameters                        |
| `disabled`         | bool | No       | -       | Whether the command is currently disabled                                                  |
| `critical`         | bool | No       | -       | Whether the command is marked as critical                                                  |
| `auto_deploy`       | bool | No       | -       | Whether to automatically deploy the command                                                |

### Schedule Configuration

The `schedule` parameter accepts a dictionary with the following sub-options:

| Parameter        | Type | Required | Description                                                                                                             |
| ---------------- | ---- | -------- | ----------------------------------------------------------------------------------------------------------------------- |
| `period`         | str  | No       | Scheduling period                                                                                                       |
| `time`           | str  | No       | Execution time in HH:mm:ss. Required when period is 'fixed_time', 'fixed_time_once' or 'start_fixed_time_and_hourly_mn' |
| `cron_expression` | str  | No       | Quartz-compatible cron expression. Required when period is 'cron_expression'                                            |
| `days_of_week`     | list | No       | List of weekdays for execution                                                                                          |

**Period Choices**: every_5min, one_per_day, hourly, manually, fixed_time, hourly_with_mn, every_minute, even_hours_with_mn, odd_hours_with_mn, even_hours, odd_hours, fixed_time_once, fixed_time_immediate, cron_expression, disabled, start_fixed_time_and_hourly_mn

**Days of Week Choices**: monday, tuesday, wednesday, thursday, friday, saturday, sunday

### History Configuration

The `history` parameter accepts a dictionary with the following sub-options:

| Parameter           | Type | Required | Description                        |
| ------------------- | ---- | -------- | ---------------------------------- |
| `document_all_runs` | bool | No       | Whether to document all executions |
| `retention`         | int  | No       | Retention time in seconds          |

### Timeout Configuration

The `timeout` parameter accepts a dictionary with the following sub-options:

| Parameter | Type | Required | Description                                |
| --------- | ---- | -------- | ------------------------------------------ |
| `type`    | str  | No       | Type of timeout (none, default, or custom) |
| `value`   | int  | No       | Timeout value in seconds (for custom type) |

**Type Choices**: none, default, custom

### Escalation Configuration

The `escalation` parameter accepts a dictionary with the following sub-options:

| Parameter           | Type | Required | Description                                  |
| ------------------- | ---- | -------- | -------------------------------------------- |
| `mail_enabled`      | bool | No       | Whether email alerts are enabled             |
| `sms_enabled`       | bool | No       | Whether SMS alerts are enabled               |
| `mail_address`      | str  | No       | Email address for alerts                     |
| `sms_address`       | str  | No       | SMS number for alerts                        |
| `min_failure_count` | int  | No       | Minimum number of failures before escalation |
| `triggers`          | dict | No       | Trigger types for escalation                 |

### Escalation Triggers

The `triggers` parameter accepts a dictionary with the following sub-options:

| Parameter      | Type | Required | Description                        |
| -------------- | ---- | -------- | ---------------------------------- |
| `every_change` | bool | No       | Currently no description available |
| `to_red`       | bool | No       | Currently no description available |
| `to_yellow`    | bool | No       | Currently no description available |
| `to_green`     | bool | No       | Currently no description available |

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

### Configure Multiple Commands

```yaml
- name: Ensure that multiple commands are configured correctly on system01
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
    - name: Configure commands
      pcg.alpaca_operator.alpaca_command_set:
        system:
          system_name: system01
        commands:
          - name: "BKP: DB log sync"
            state: present
            agent_name: agent01
            parameters: "-p GLTarch -s <BKP_LOG_SRC> -l 4 -d <BKP_LOG_DEST1> -r <BKP_LOG_DEST2> -b <BKP_LOG_CLEANUP_INT> -t <BKP_LOG_CLEANUP_INT2> -h DB_HOST"
            process_central_id: 8990048
            schedule:
              period: manually
              time: "01:00:00"
              days_of_week:
                - monday
                - sunday
            parameters_needed: false
            disabled: false
            critical: true
            history:
              document_all_runs: true
              retention: 900
            auto_deploy: false
            timeout:
              type: default
              value: 30
            escalation:
              mail_enabled: true
              sms_enabled: true
              mail_address: "monitoring@pcg.io"
              sms_address: "0123456789"
              min_failure_count: 1
              triggers:
                every_change: true
                to_red: false
                to_yellow: false
                to_green: true
          - name: "BKP: DB log sync 2"
            state: present
            agent_name: agent02
            parameters: "-p GLTarch -s <BKP_LOG_SRC> -l 4 -d <BKP_LOG_DEST1> -r <BKP_LOG_DEST2> -b <BKP_LOG_CLEANUP_INT> -t <BKP_LOG_CLEANUP_INT2> -h DB_HOST"
            process_central_id: 8990048
            schedule:
              period: cron_expression
              cron_expression: '0 */5 * * * ?'
            parameters_needed: false
            disabled: false
            critical: true
            history:
              document_all_runs: true
              retention: 900
            auto_deploy: false
            timeout:
              type: default
              value: 30
            escalation:
              mail_enabled: true
              sms_enabled: true
              mail_address: "monitoring@pcg.io"
              sms_address: "0123456789"
              min_failure_count: 1
              triggers:
                every_change: true
                to_red: false
                to_yellow: false
                to_green: true
        api_connection: "{{ api_connection }}"
```

### Remove All Commands

```yaml
- name: Remove all commands from system system01
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
    - name: Remove all commands
      pcg.alpaca_operator.alpaca_command_set:
        system:
          system_name: system01
        commands: []
        api_connection: "{{ api_connection }}"
```

## Return Values

| Parameter | Type | Returned                  | Description                                                       |
| --------- | ---- | ------------------------- | ----------------------------------------------------------------- |
| `msg`     | str  | always                    | Status message                                                    |
| `changed` | bool | always                    | Whether any change was made                                       |
| `changes` | dict | when changes are detected | A dictionary describing all changes that were or would be applied |

### Changes Dictionary Structure

The `changes` dictionary typically follows the format `commandIndex_XXX`, representing the index in the `commands` list. Each entry includes diffs between the current and desired state. Also includes `removed_commands` if commands were deleted.

#### Example Changes Structure

```json
{
  "commandIndex_000": {
    "parameters": {
      "current": "-p foo -s A -d B",
      "desired": "-p foo -s A -d B -t X"
    },
    "schedule": {
      "period": {
        "current": "manually",
        "desired": "every_minute"
      }
    }
  },
  "commandIndex_001": {
    "escalation": {
      "min_failure_count": {
        "current": 0,
        "desired": 1
      }
    }
  },
  "removed_commands": [
    "Old Command Name 1",
    "Old Command Name 2"
  ]
}
```

## Notes

- **Critical Warning**: This module takes full control of the command set. Any commands not defined in the `commands` list will be removed from the system.
- The module supports check mode for previewing changes without applying them
- Commands are uniquely identified by name and agent assignment
- When updating existing commands, only specified fields are modified
- The agent must be assigned to the corresponding system if managed via Ansible
- Schedule configurations support various periodic execution patterns including cron expressions
- Escalation settings can be configured for both email and SMS notifications
- Use this module for bulk operations rather than individual command management
- Empty commands list will remove all commands from the system
- API connection variables should be stored in the inventory file and referenced via `api_connection: "{{ api_connection }}"` in playbooks

## Author

- Jan-Karsten Hansmeyer (@pcg)