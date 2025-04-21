from napalm import get_network_driver
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoAuthenticationException, NetMikoTimeoutException

class HybridNetworkDevice:
    def __init__(self, hostname, ip, username, password):
        self.hostname = hostname
        self.ip = ip
        self.username = username
        self.password = password
        self.device_os = None
        self.napalm_driver = None
        self.netmiko_conn = None

        self.detect_device_type()  # ← Automatically determine on instantiation

    def detect_device_type(self):
        """Try each NAPALM driver to detect the device OS and open a NAPALM session if successful."""
        for driver_name in ['ios', 'iosxr', 'nxos', 'eos', 'asa']:
            try:
                driver = get_network_driver(driver_name)
                device = driver(self.ip, self.username, self.password)
                device.open()
                facts = device.get_facts()
                self.napalm_driver = device
                self.device_os = driver_name
                print(f"[+] Detected OS via NAPALM: {driver_name}")
                return
            except Exception:
                continue

        print("[-] Unable to detect OS with NAPALM")
        self.device_os = "unknown"

    def connect_netmiko(self):
        """Establish a Netmiko connection using the detected OS."""
        device_type_map = {
            'ios': 'cisco_ios',
            'iosxr': 'cisco_xr',
            'nxos': 'cisco_nxos',
            'eos': 'arista_eos',
            'asa': 'cisco_asa',
        }

        try:
            self.netmiko_conn = ConnectHandler(
                device_type=device_type_map.get(self.device_os, 'cisco_ios'),
                ip=self.ip,
                username=self.username,
                password=self.password
            )
            print("[+] Netmiko connected")
        except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
            print(f"[-] Netmiko connection failed: {e}")

    def run_command(self, command):
        """Run command using Netmiko."""
        if not self.netmiko_conn:
            self.connect_netmiko()
        return self.netmiko_conn.send_command(command)

    def get_cdp_neighbors(self):
        """Fetch CDP neighbors via Netmiko."""
        return self.run_command("show cdp neighbors detail")

    def disconnect(self):
        """Cleanup both NAPALM and Netmiko sessions."""
        if self.napalm_driver:
            self.napalm_driver.close()
        if self.netmiko_conn:
            self.netmiko_conn.disconnect()