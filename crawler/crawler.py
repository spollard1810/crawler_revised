from core.device_handler import DeviceHandler

class Crawler:
    def __init__(self, hostname_or_ip, username, password, validate=False):
        self.device = DeviceHandler(hostname_or_ip, username, password, validate)

