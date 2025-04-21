from .connector import HybridNetworkDeviceBuilder
from .command_sender import CommandSender
from .command_parser import CommandParser

class DeviceHandler:
    def __init__(self, hostname_or_ip, username, password, validate=False):
        self.device = (
            HybridNetworkDeviceBuilder(hostname_or_ip)
            .with_credentials(username, password)
            .with_validation(validate)
            .build()
        )

        self.sender = CommandSender(self.device)
        self.parser = CommandParser()
        
        # Store device type for consistent parsing
        # Map ios_xe to ios for template parsing since they share the same format
        self.device_type = 'ios' if self.device.device_os == 'cisco_xe' else self.device.device_os

    def _parse_output(self, command, raw_output):
        """Helper method to consistently parse command output"""
        return self.parser.parse(command, raw_output, self.device_type)

    def run(self, command):
        """Run a command and return raw output"""
        return self.sender.send_custom(command)

    def run_and_parse(self, command):
        """Run a command and return parsed output"""
        raw = self.sender.send_custom(command)
        return self._parse_output(command, raw)

    def get_cdp_neighbors(self):
        """Get and parse CDP neighbor information"""
        raw = self.sender.get_cdp_neighbors()
        print(f"[DEBUG] Raw CDP output:\n{raw}")
        parsed = self._parse_output("show cdp neighbors detail", raw)
        print(f"[DEBUG] Parsed CDP output:\n{parsed}")
        return parsed

    def get_lldp_neighbors(self):
        """Get and parse LLDP neighbor information"""
        raw = self.sender.get_lldp_neighbors()
        return self._parse_output("show lldp neighbors detail", raw)

    def get_version_info(self):
        """Get and parse version information"""
        raw = self.sender.get_version_info()
        return self._parse_output("show version", raw)

    def disconnect(self):
        """Disconnect from the device"""
        self.device.disconnect()