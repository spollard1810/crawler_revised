from ntc_templates.parse import parse_output

class CommandParser:
    def _convert_to_ntc_platform(self, device_type):
        """Convert device type to NTC templates platform format."""
        platform_map = {
            'ios': 'cisco_ios',
            'xe': 'cisco_ios',  # Cisco XE uses the same templates as IOS
            'nxos': 'cisco_nxos',
            'cisco_ios': 'cisco_ios',
            'cisco_xe': 'cisco_ios',
            'cisco_nxos': 'cisco_nxos'
        }
        return platform_map.get(device_type.lower(), device_type)

    def parse(self, command, raw_output, netmiko_os):
        try:
            ntc_platform = self._convert_to_ntc_platform(netmiko_os)
            parsed = parse_output(
                platform=ntc_platform,
                command=command,
                data=raw_output
            )
            return parsed
        except Exception as e:
            print(f"[-] Failed to parse output for {command}: {e}")
            print(f"[DEBUG] Raw output that failed to parse:\n{raw_output}")
            return None