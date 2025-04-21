from ntc_templates.parse import parse_output

class CommandParser:
    def parse(self, command, raw_output, netmiko_os):
        try:
            print(f"[DEBUG] Parsing command: {command}")
            print(f"[DEBUG] Using platform: {netmiko_os}")
            parsed = parse_output(
                platform=netmiko_os,
                command=command,
                data=raw_output
            )
            return parsed
        except Exception as e:
            print(f"[-] Failed to parse output for {command}: {e}")
            print(f"[DEBUG] Raw output that failed to parse:\n{raw_output}")
            return None