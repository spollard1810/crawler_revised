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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
