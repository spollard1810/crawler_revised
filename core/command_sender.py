class CommandSender:
    def __init__(self, device):
        self.device = device  # An instance of HybridNetworkDevice

    def get_cdp_neighbors(self):
        return self.device.run_command("show cdp neighbors detail")

    def get_lldp_neighbors(self):
        return self.device.run_command("show lldp neighbors detail")

    def get_version_info(self):
        return self.device.run_command("show version")

    def send_custom(self, command):
        return self.device.run_command(command)