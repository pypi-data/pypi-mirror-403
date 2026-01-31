# ALPACA Command Module

## Overview

The `pcg.alpaca_operator.alpaca_command` module manages a single [ALPACA Operator](https://alpaca.pcg.io/) command. It provides fine-grained control over individual command properties. Use this module when you need to configure or modify one specific command, such as changing its timeout, toggling disabled, or setting a new schedule.

Each command is uniquely identified by the combination of its name (description) and the assigned agentHostname. Note that renaming a command or reassigning it to a different agent is not supported by this module, as these properties are used for identification.

## Module Information

- **Module Name**: `pcg.alpaca_operator.alpaca_command`
- **Short Description**: Manage a single ALPACA Operator command via REST API
- **Version Added**: 1.0.0
- **Requirements**:
  - Python >= 3.8
  - ansible-core >= 2.12
  - ALPACA Operator >= 5.6.0

## Update Behavior

If the desired command already exists, only the fields required for unique identification need to be provided (i.e., either system_id or system_name, and either agent_id or agent_name). Any options not explicitly set in the module call or the playbook will retain their existing values from the current configuration.

## Parameters

### Required Parameters

| Parameter        | Type | Required | Description                                                                                        |
| ---------------- | ---- | -------- | -------------------------------------------------------------------------------------------------- |
| `system`         | dict | Yes      | Dictionary containing system identification. Either `system_id` or `system_name` must be provided. |
| `command`        | dict | Yes      | Definition of the desired command                                                                  |
| `api_connection` | dict | Yes      | Connection details for accessing the ALPACA Operator API                                           |

### System Identification

The `system` parameter accepts a dictionary with the following sub-options:

| Parameter     | Type | Required | Description                                                             |
| ------------- | ---- | -------- | ----------------------------------------------------------------------- |
| `system_id`   | int  | No*      | Numeric ID of the target system. Optional if `system_name` is provided. |
| `system_name` | str  | No*      | Name of the target system. Optional if `system_id` is provided.         |

*Either `system_id` or `system_name` must be provided.

### Command Configuration

The `command` parameter accepts a dictionary with the following sub-options:

| Parameter            | Type | Required | Default | Description                                                                                 |
| -------------------- | ---- | -------- | ------- | ------------------------------------------------------------------------------------------- |
| `name`               | str  | No       | -       | Name or description of the command                                                          |
| `state`              | str  | No       | present | Desired state of the command (present, absent)                                              |
| `agent_id`           | int  | No       | -       | Numeric ID of the agent. Optional if `agent_name` is provided.                              |
| `agent_name`         | str  | No       | -       | Name of the agent. Optional if `agent_id` is provided.                                      |
| `process_id`         | int  | No       | -       | ID of the process to be executed. Optional if `process_central_id` is provided.             |
| `process_central_id` | int  | No       | -       | Central ID / Global ID of the process to be executed. Optional if `process_id` is provided. |
| `parameters`         | str  | No       | -       | Parameters for the process                                                                  |
| `parameters_needed`  | bool | No       | -       | Whether the execution of the command requires additional parameters                         |
| `disabled`           | bool | No       | -       | Whether the command is currently disabled                                                   |
| `critical`           | bool | No       | -       | Whether the command is marked as critical                                                   |
| `auto_deploy`        | bool | No       | -       | Whether to automatically deploy the command                                                 |

### Schedule Configuration

The `schedule` parameter accepts a dictionary with the following sub-options:

| Parameter         | Type | Required | Description                                                                                                             |
| ----------------- | ---- | -------- | ----------------------------------------------------------------------------------------------------------------------- |
| `period`          | str  | No       | Scheduling period                                                                                                       |
| `time`            | str  | No       | Execution time in HH:mm:ss. Required when period is 'fixed_time', 'fixed_time_once' or 'start_fixed_time_and_hourly_mn' |
| `cron_expression` | str  | No       | Quartz-compatible cron expression. Required when period is 'cron_expression'                                            |
| `days_of_week`    | list | No       | List of weekdays for execution                                                                                          |

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

### Create a Command

```yaml
- name: Ensure a specific system command exist
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
    - name: Create command
      pcg.alpaca_operator.alpaca_command:
        system:
          system_name: system01
        command:
          name: "BKP: DB log sync"
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
        api_connection: "{{ api_connection }}"
```

### Delete a Command

```yaml
- name: Delete a specific command
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
    - name: Delete command
      pcg.alpaca_operator.alpaca_command:
        system:
          system_name: system01
        command:
          name: "BKP: DB log sync"
          agent_name: agent01
          state: absent
        api_connection: "{{ api_connection }}"
```

## Return Values

| Parameter | Type | Returned                                  | Description                                                                                 |
| --------- | ---- | ----------------------------------------- | ------------------------------------------------------------------------------------------- |
| `msg`     | str  | always                                    | Status message describing what the module did                                               |
| `changed` | bool | always                                    | Whether any changes were made                                                               |
| `changes` | dict | when changes are detected                 | Dictionary containing the differences between the current and desired command configuration |
| `payload` | dict | when state is present and change occurred | Full payload that would be sent to the API (in check_mode) or that was sent (when changed)  |

### Return Value Examples

#### Command Update with Changes

```json
{
  "msg": "Command updated in system 42.",
  "changed": true,
  "changes": {
    "parameters": {
      "current": "-p foo -s A -d B",
      "desired": "-p foo -s A -d B -t X"
    },
    "schedule": {
      "period": {
        "current": "manually",
        "desired": "every_minute"
      }
    },
    "escalation": {
      "min_failure_count": {
        "current": 0,
        "desired": 1
      }
    }
  }
}
```

## Notes

- The module supports check mode for previewing changes without applying them
- Commands are uniquely identified by name and agent assignment
- Renaming commands or reassigning to different agents is not supported
- When updating existing commands, only specified fields are modified
- The agent must be assigned to the corresponding system if managed via Ansible
- Schedule configurations support various periodic execution patterns
- Escalation settings can be configured for both email and SMS notifications
- API connection variables should be stored in the inventory file and referenced via `api_connection: "{{ api_connection }}"` in playbooks

## Author

- Jan-Karsten Hansmeyer (@pcg)