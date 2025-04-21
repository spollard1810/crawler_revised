from core.device_handler import DeviceHandler

# Create a device handler
handler = DeviceHandler("192.168.1.1", "admin", "password")

# Get raw output
raw_output = handler.run("show interface")

# Get parsed output
parsed_output = handler.run_and_parse("show interface")

# Get structured neighbor information
cdp_neighbors = handler.get_cdp_neighbors()
lldp_neighbors = handler.get_lldp_neighbors()

# Get version information
version_info = handler.get_version_info()

# Clean up
handler.disconnect()