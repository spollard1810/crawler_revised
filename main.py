from core import DeviceHandler
from crawler import Crawler

#test cases for core
#handler = DeviceHandler("192.168.1.1", "admin", "password")

#raw_output = handler.run("show interface")

#parsed_output = handler.run_and_parse("show interface")


crawler = (
    Crawler()
    .with_seed_device("192.168.1.1", "admin", "secret")
    .with_workers(5)
    .with_debug(True)
    .build()
)

# Start the crawler
crawler.start()