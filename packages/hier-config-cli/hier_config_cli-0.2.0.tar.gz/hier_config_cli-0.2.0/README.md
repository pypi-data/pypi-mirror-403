# Hier Config CLI

[![PyPI version](https://badge.fury.io/py/hier-config-cli.svg)](https://badge.fury.io/py/hier-config-cli)
[![Python Versions](https://img.shields.io/pypi/pyversions/hier-config-cli.svg)](https://pypi.org/project/hier-config-cli/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Tests](https://github.com/netdevops/hier-config-cli/workflows/test-app/badge.svg)](https://github.com/netdevops/hier-config-cli/actions)

A powerful command-line interface tool for network configuration analysis, remediation, and rollback built on top of the [Hier Config](https://github.com/netdevops/hier_config) library.

## Overview

**hier-config-cli** helps network engineers analyze configuration differences, generate remediation commands, prepare rollback procedures, and predict configuration states across multiple network platforms. It's an essential tool for network automation workflows, change management, and configuration compliance.

### Key Features

- 🔄 **Remediation Generation**: Automatically generate commands to transform running config into intended config
- ⏮️ **Rollback Planning**: Create rollback procedures before making changes
- 🔮 **Future State Prediction**: Preview the complete configuration after applying changes
- 🌐 **Multi-Platform Support**: Works with Cisco, Juniper, Arista, HP, Fortinet, VyOS, and more
- 📊 **Multiple Output Formats**: Export as text, JSON, or YAML
- 🎯 **Type-Safe**: Fully typed Python code with mypy support
- ✅ **Well-Tested**: Comprehensive test suite with high code coverage
- 📝 **Detailed Logging**: Verbose and debug modes for troubleshooting

## Installation

### Via pip (recommended)

```bash
pip install hier-config-cli
```

### Via Poetry

```bash
poetry add hier-config-cli
```

### From Source

```bash
git clone https://github.com/netdevops/hier-config-cli.git
cd hier-config-cli
poetry install
```

## Quick Start

### 1. List Available Platforms

```bash
hier-config-cli list-platforms
```

Output:
```
=== Available Platforms ===
  eos
  fortios
  generic
  hp_comware5
  hp_procurve
  ios
  iosxr
  junos
  nxos
  vyos
```

### 2. Generate Remediation Configuration

Compare your running configuration with the intended configuration and generate the commands needed to remediate:

```bash
hier-config-cli remediation \
  --platform ios \
  --running-config running.conf \
  --generated-config intended.conf
```

### 3. Generate Rollback Configuration

Prepare rollback commands before making changes:

```bash
hier-config-cli rollback \
  --platform ios \
  --running-config running.conf \
  --generated-config intended.conf
```

### 4. Preview Future Configuration

See what the complete configuration will look like after applying changes:

```bash
hier-config-cli future \
  --platform ios \
  --running-config running.conf \
  --generated-config intended.conf
```

## Usage Examples

### Basic Remediation

```bash
hier-config-cli remediation \
  --platform ios \
  --running-config examples/cisco_ios_running.conf \
  --generated-config examples/cisco_ios_intended.conf
```

Output:
```
=== Remediation Configuration ===
no hostname router-01
hostname router-01-updated
interface GigabitEthernet0/0
 no description WAN Interface
 description WAN Interface - Updated
interface Vlan20
 description Guest VLAN
 ip address 10.0.20.1 255.255.255.0
router ospf 1
 network 10.0.20.0 0.0.0.255 area 0
ntp server 192.0.2.1
```

### Export to JSON

```bash
hier-config-cli remediation \
  --platform ios \
  --running-config running.conf \
  --generated-config intended.conf \
  --format json
```

### Export to YAML

```bash
hier-config-cli remediation \
  --platform nxos \
  --running-config running.conf \
  --generated-config intended.conf \
  --format yaml
```

### Save Output to File

```bash
hier-config-cli remediation \
  --platform iosxr \
  --running-config running.conf \
  --generated-config intended.conf \
  --output remediation_commands.txt
```

### Enable Verbose Logging

```bash
# INFO level logging
hier-config-cli -v remediation \
  --platform ios \
  --running-config running.conf \
  --generated-config intended.conf

# DEBUG level logging
hier-config-cli -vv remediation \
  --platform ios \
  --running-config running.conf \
  --generated-config intended.conf
```

## Commands

### `remediation`

Generates the commands needed to transform the running configuration into the intended configuration.

**Options:**
- `--platform`: Target platform (required) - see `list-platforms` for options
- `--running-config`: Path to running configuration file (required)
- `--generated-config`: Path to intended/generated configuration file (required)
- `--format`: Output format - `text`, `json`, or `yaml` (default: text)
- `--output, -o`: Write output to file instead of stdout

### `rollback`

Generates the commands needed to revert from the intended configuration back to the running configuration. Useful for preparing rollback procedures before making changes.

**Options:** Same as `remediation`

### `future`

Predicts what the complete configuration will look like after applying the intended configuration to the running configuration.

**Options:** Same as `remediation`

### `list-platforms`

Lists all supported network platforms.

### `version`

Shows the installed version of hier-config-cli.

## Supported Platforms

| Platform | Code | Description |
|----------|------|-------------|
| Cisco IOS | `ios` | Cisco IOS routers and switches |
| Cisco NX-OS | `nxos` | Cisco Nexus switches |
| Cisco IOS XR | `iosxr` | Cisco IOS XR routers |
| Arista EOS | `eos` | Arista switches |
| Juniper JunOS | `junos` | Juniper routers and switches |
| VyOS | `vyos` | VyOS routers |
| Fortinet FortiOS | `fortios` | Fortinet firewalls |
| HP Comware5 | `hp_comware5` | HP Comware5 switches |
| HP ProCurve | `hp_procurve` | HP ProCurve switches |
| Generic | `generic` | Generic/unknown platform |

## Integration Examples

### With Nornir

```python
from nornir import InitNornir
from nornir.core.task import Task
import subprocess

def generate_remediation(task: Task) -> None:
    """Generate remediation for a device."""
    result = subprocess.run(
        [
            "hier-config-cli",
            "remediation",
            "--platform", task.host.platform,
            "--running-config", f"configs/{task.host.name}_running.conf",
            "--generated-config", f"configs/{task.host.name}_intended.conf",
            "--output", f"remediation/{task.host.name}_remediation.txt",
        ],
        capture_output=True,
        text=True,
    )
    return result.stdout

nr = InitNornir(config_file="config.yaml")
results = nr.run(task=generate_remediation)
```

### With Ansible

```yaml
- name: Generate configuration remediation
  hosts: network_devices
  tasks:
    - name: Run hier-config-cli remediation
      command: >
        hier-config-cli remediation
        --platform {{ platform }}
        --running-config /tmp/{{ inventory_hostname }}_running.conf
        --generated-config /tmp/{{ inventory_hostname }}_intended.conf
        --output /tmp/{{ inventory_hostname }}_remediation.txt
      register: remediation_result

    - name: Display remediation
      debug:
        msg: "{{ remediation_result.stdout }}"
```

### In CI/CD Pipeline

```yaml
# .github/workflows/config-validation.yml
name: Validate Network Configs

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install hier-config-cli
        run: pip install hier-config-cli

      - name: Generate remediation
        run: |
          hier-config-cli remediation \
            --platform ios \
            --running-config prod/running.conf \
            --generated-config staging/intended.conf \
            --output remediation.txt

      - name: Upload remediation
        uses: actions/upload-artifact@v4
        with:
          name: remediation-config
          path: remediation.txt
```

## Development

### Prerequisites

- Python 3.9 or higher
- Poetry (for dependency management)

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/netdevops/hier-config-cli.git
cd hier-config-cli

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=hier_config_cli --cov-report=html

# Run specific test file
pytest tests/test_cli.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Type check with mypy
mypy src/

# Run all quality checks
black src/ tests/ && ruff check src/ tests/ && mypy src/ && pytest
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on:

- Code of conduct
- Development workflow
- Pull request process
- Coding standards

## Security

For security issues, please see [SECURITY.md](SECURITY.md) for our security policy and how to report vulnerabilities.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed list of changes between versions.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Links

- **Documentation**: [https://github.com/netdevops/hier-config-cli](https://github.com/netdevops/hier-config-cli)
- **PyPI**: [https://pypi.org/project/hier-config-cli/](https://pypi.org/project/hier-config-cli/)
- **Issues**: [https://github.com/netdevops/hier-config-cli/issues](https://github.com/netdevops/hier-config-cli/issues)
- **Hier Config Library**: [https://github.com/netdevops/hier_config](https://github.com/netdevops/hier_config)

## Acknowledgments

Built on top of the excellent [Hier Config](https://github.com/netdevops/hier_config) library by James Williams and contributors.

## Support

- 📫 Open an issue: [GitHub Issues](https://github.com/netdevops/hier-config-cli/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/netdevops/hier-config-cli/discussions)
- 📧 Email: james.williams@packetgeek.net
