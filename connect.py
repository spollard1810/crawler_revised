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

        self.detect_device_type()  # Auto-detect at instantiation

    def detect_device_type(self):
        """Try NAPALM drivers, fallback to Netmiko 'show version' if needed."""

        print(f"[~] Starting device detection for {self.hostname} ({self.ip})")

        # Prefer nxos before ios to avoid misdetection
        for driver_name in ['nxos', 'iosxr', 'ios', 'eos', 'asa']:
            try:
                driver = get_network_driver(driver_name)
                device = driver(self.ip, self.username, self.password)
                device.open()
                facts = device.get_facts()
                self.napalm_driver = device
                self.device_os = driver_name
                print(f"[+] Detected OS via NAPALM: {driver_name}")
                return
            except Exception as e:
                print(f"[-] NAPALM failed with {driver_name}: {e}")

        # Fallback to Netmiko + 'show version' parsing
        print("[~] Falling back to Netmiko for OS detection")
        try:
            self.netmiko_conn = ConnectHandler(
                device_type='cisco_ios',  # Generic CLI driver
                ip=self.ip,
                username=self.username,
                password=self.password
            )
            output = self.netmiko_conn.send_command("show version")
            if "NX-OS" in output:
                self.device_os = "nxos"
            elif "IOS XR" in output:
                self.device_os = "iosxr"
            elif "Arista" in output:
                self.device_os = "eos"
            elif "Adaptive Security Appliance" in output:
                self.device_os = "asa"
            else:
                self.device_os = "ios"
            print(f"[+] Fallback detection via CLI: {self.device_os}")
        except Exception as e:
            print(f"[-] Netmiko fallback detection failed: {e}")
            self.device_os = "unknown"

    def connect_netmiko(self):
        """Establish a Netmiko connection using the detected OS."""
        if self.netmiko_conn:
            return  # Already connected

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
            self.netmiko_conn = None

    def run_command(self, command):
        """Run command using Netmiko."""
        if not self.netmiko_conn:
            self.connect_netmiko()
        if self.netmiko_conn:
            return self.netmiko_conn.send_command(command)
        else:
            print("[-] Unable to run command: Netmiko not connected.")
            return None

    def get_cdp_neighbors(self):
        """Fetch CDP neighbors via Netmiko."""
        return self.run_command("show cdp neighbors detail")

    def get_lldp_neighbors(self):
        """Fetch LLDP neighbors via Netmiko (fallback for non-Cisco)."""
        return self.run_command("show lldp neighbors detail")

    def get_facts(self):
        """Return NAPALM facts if available."""
        if self.napalm_driver:
            return self.napalm_driver.get_facts()
        return {}

    def disconnect(self):
        """Cleanup both NAPALM and Netmiko sessions."""
        if self.napalm_driver:
            self.napalm_driver.close()
        if self.netmiko_conn:
            self.netmiko_conn.disconnect()