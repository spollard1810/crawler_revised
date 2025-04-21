from ntc_templates.parse import parse_output

class CommandParser:
    def parse(self, command, raw_output, netmiko_os):
        try:
            parsed = parse_output(
                platform=netmiko_os,
                command=command,
                data=raw_output
            )
            return parsed
        except Exception as e:
            print(f"[-] Failed to parse output for {command}: {e}")
            return None