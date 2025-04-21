from netmiko import ConnectHandler
from netmiko.ssh_autodetect import SSHDetect
from netmiko.exceptions import NetMikoAuthenticationException, NetMikoTimeoutException


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

    def disconnect(self):
        if self.netmiko_conn:
            try:
                self.netmiko_conn.disconnect()
            except Exception:
                pass
    def get_OS(self):
        return self.device_os
