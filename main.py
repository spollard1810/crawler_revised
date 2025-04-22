from core import DeviceHandler
from crawler import Crawler

#test cases for core
handler = DeviceHandler("192.168.1.1", "admin", "password")

raw_output = handler.run("show interface")

parsed_output = handler.run_and_parse("show interface")



# Crawler builder