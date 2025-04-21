# Command Execution Orchestration Platform for Network Devices

A Python-based platform for orchestrating and executing commands on network devices, with a focus on Cisco devices. This platform provides a unified interface for device interaction, command execution, and output parsing.

## Features

- Device connection and authentication management
- Raw command execution
- Structured command output parsing
- CDP neighbor discovery
- Version information retrieval
- Support for multiple device types
- Automatic device type detection

## Prerequisites

- Python 3.6+
- Network access to target devices
- Valid device credentials

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd crawler_revised
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Dependencies

- netmiko: Multi-vendor library to simplify Paramiko SSH connections to network devices
- ntc-templates: TextFSM templates for parsing show commands

## Usage

```python
from core.device_handler import DeviceHandler

# Initialize device handler
handler = DeviceHandler("192.168.1.1", "admin", "password")

# Execute raw commands
raw_output = handler.run("show interface")

# Execute and parse commands
parsed_output = handler.run_and_parse("show interface")

# Get CDP neighbor information
cdp_neighbors = handler.get_cdp_neighbors()

# Get device version information
version_info = handler.get_version_info()

# Get device inventory information
inventory_info = handler.get_inventory()

# Clean up connection
handler.disconnect()
```

## Project Structure

```
crawler_revised/
├── core/               # Core functionality modules
├── main.py            # Example usage
├── requirements.txt   # Project dependencies
└── readme.md         # Documentation
```

## Class Breakdown

### DeviceHandler
The main interface class for interacting with network devices.

- `__init__(hostname_or_ip, username, password, validate=False)`: Initializes the device handler with connection details
- `run(command)`: Executes a raw command and returns unparsed output
- `run_and_parse(command)`: Executes a command and returns structured, parsed output
- `get_cdp_neighbors()`: Retrieves and parses CDP neighbor information
- `get_lldp_neighbors()`: Retrieves and parses LLDP neighbor information
- `get_version_info()`: Retrieves and parses device version information
- `get_inventory()`: Retrieves and parses device inventory information
- `disconnect()`: Closes the device connection

### CommandSender
Handles the execution of commands on network devices.

- `__init__(device)`: Initializes with a device connection
- `get_cdp_neighbors()`: Sends CDP neighbor discovery command
- `get_lldp_neighbors()`: Sends LLDP neighbor discovery command
- `get_version_info()`: Sends version information command
- `send_custom(command)`: Sends a custom command to the device

### CommandParser
Manages the parsing of command outputs into structured data.

- `parse(command, raw_output, netmiko_os)`: Parses raw command output into structured data
- `_convert_to_ntc_platform(device_type)`: Converts device types to NTC templates format

### HybridNetworkDevice
Core class for device connectivity and command execution.

- `__init__(hostname_or_ip, username, password)`: Initializes device connection parameters
- `detect_os_and_initialize()`: Automatically detects device operating system
- `connect_netmiko()`: Establishes Netmiko connection
- `run_command(command)`: Executes a command on the device
- `disconnect()`: Closes the device connection
- `get_OS()`: Returns the detected device operating system

### HybridNetworkDeviceBuilder
Builder pattern implementation for creating device connections.

- `__init__(hostname_or_ip)`: Initializes builder with device address
- `with_credentials(username, password)`: Sets device credentials
- `with_validation(validate)`: Enables/disables host validation
- `_ping_host()`: Validates host reachability
- `build()`: Creates and returns a configured device instance

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
