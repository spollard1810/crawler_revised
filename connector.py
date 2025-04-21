import subprocess
import platform
from netmiko import ConnectHandler
from netmiko.ssh_autodetect import SSHDetect
from netmiko.exceptions import NetMikoAuthenticationException, NetMikoTimeoutException


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
    def __init__(self, hostname_or_ip, username, password):
        self.hostname = hostname_or_ip
        self.ip = hostname_or_ip
        self.username = username
        self.password = password
        self.device_os = None
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
            self.device_os = guesser.autodetect()

            if not self.device_os:
                raise Exception("SSHDetect failed to determine device type")

            print(f"[+] Netmiko detected OS: {self.device_os}")

        except Exception as e:
            print(f"[-] SSHDetect failed: {e}")
            self.device_os = "unknown"

    def connect_netmiko(self):
        if self.netmiko_conn:
            return

        try:
            self.netmiko_conn = ConnectHandler(
                device_type=self.device_os or 'cisco_ios',
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

    def get_version_info(self):
        return self.run_command("show version")

    def disconnect(self):
        if self.netmiko_conn:
            try:
                self.netmiko_conn.disconnect()
            except Exception:
                pass