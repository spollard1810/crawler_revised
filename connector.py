import subprocess
import platform
from netmiko import ConnectHandler
from netmiko.ssh_autodetect import SSHDetect
from netmiko.exceptions import NetMikoAuthenticationException, NetMikoTimeoutException
from napalm import get_network_driver


class HybridNetworkDeviceBuilder:
    def __init__(self, hostname_or_ip):
        self.hostname_or_ip = hostname_or_ip
        self.username = None
        self.password = None
        self.validate_reachability = False

    def with_credentials(self, username, password):
        self.username = username
        self.password = password
        return self

    def with_validation(self, enable=True):
        self.validate_reachability = enable
        return self

    def _is_reachable(self):
        """Ping the host before attempting SSH detection."""
        count_flag = "-n" if platform.system().lower() == "windows" else "-c"
        try:
            result = subprocess.run(
                ["ping", count_flag, "2", self.hostname_or_ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return result.returncode == 0
        except Exception as e:
            print(f"[!] Ping failed: {e}")
            return False

    def build(self):
        if not self.username or not self.password:
            raise ValueError("Username and password must be provided before building.")

        if self.validate_reachability:
            print(f"[~] Validating reachability to {self.hostname_or_ip}...")
            if not self._is_reachable():
                raise ConnectionError(f"Host {self.hostname_or_ip} is unreachable (ping failed).")

        return HybridNetworkDevice(
            hostname_or_ip=self.hostname_or_ip,
            username=self.username,
            password=self.password
        )
class HybridNetworkDevice:
    NETMIKO_TO_NAPALM = {
        'cisco_ios': 'ios',
        'cisco_xr': 'iosxr',
        'cisco_nxos': 'nxos',
        'arista_eos': 'eos',
        'cisco_asa': 'asa'
    }

    def __init__(self, hostname_or_ip, username, password):
        self.hostname = hostname_or_ip
        self.ip = hostname_or_ip
        self.username = username
        self.password = password
        self.device_os_netmiko = None
        self.device_os_napalm = None
        self.napalm_driver = None
        self.netmiko_conn = None

        self.detect_os_and_initialize()

    def detect_os_and_initialize(self):
        print(f"[~] Running SSHDetect for {self.hostname}")

        try:
            guesser = SSHDetect(
                device_type='autodetect',
                host=self.ip,
                username=self.username,
                password=self.password
            )
            self.device_os_netmiko = guesser.autodetect()

            if not self.device_os_netmiko:
                raise Exception("SSHDetect failed to determine device type")

            print(f"[+] Netmiko detected OS: {self.device_os_netmiko}")

            self.device_os_napalm = self.NETMIKO_TO_NAPALM.get(self.device_os_netmiko)

            if self.device_os_napalm:
                try:
                    driver = get_network_driver(self.device_os_napalm)
                    device = driver(self.ip, self.username, self.password)
                    device.open()
                    self.napalm_driver = device
                    print(f"[+] NAPALM session opened with {self.device_os_napalm}")
                except Exception as e:
                    print(f"[-] Failed to open NAPALM session: {e}")
            else:
                print(f"[-] No NAPALM driver mapped for {self.device_os_netmiko}")

        except Exception as e:
            print(f"[-] SSHDetect failed: {e}")
            self.device_os_netmiko = "unknown"

    def connect_netmiko(self):
        if self.netmiko_conn:
            return

        try:
            self.netmiko_conn = ConnectHandler(
                device_type=self.device_os_netmiko or 'cisco_ios',
                ip=self.ip,
                username=self.username,
                password=self.password
            )
            print("[+] Netmiko connected")
        except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
            print(f"[-] Netmiko connection failed: {e}")
            self.netmiko_conn = None

    def run_command(self, command):
        if not self.netmiko_conn:
            self.connect_netmiko()
        if self.netmiko_conn:
            return self.netmiko_conn.send_command(command)
        else:
            print("[-] Netmiko not connected.")
            return None

    def get_cdp_neighbors(self):
        return self.run_command("show cdp neighbors detail")

    def get_lldp_neighbors(self):
        return self.run_command("show lldp neighbors detail")

    def get_facts(self):
        if self.napalm_driver:
            try:
                return self.napalm_driver.get_facts()
            except Exception as e:
                print(f"[-] Failed to get facts: {e}")
        return {}

    def disconnect(self):
        if self.napalm_driver:
            try:
                self.napalm_driver.close()
            except Exception:
                pass
        if self.netmiko_conn:
            try:
                self.netmiko_conn.disconnect()
            except Exception:
                pass