from typing import Optional
from .data import Database
from .crawler import NetworkCrawler
from .fsm import DeviceFSM

class CrawlerBuilder:
    def __init__(self):
        self._seed_ip: Optional[str] = None
        self._username: Optional[str] = None
        self._password: Optional[str] = None
        self._max_workers: int = 5
        self._db_path: str = "netparse.db"
        self._debug: bool = False
        self._crawler: Optional[NetworkCrawler] = None

    def with_seed_device(self, ip: str, username: str, password: str) -> 'CrawlerBuilder':
        """Configure the seed device and credentials."""
        self._seed_ip = ip
        self._username = username
        self._password = password
        return self

    def with_workers(self, count: int) -> 'CrawlerBuilder':
        """Set the number of worker threads."""
        self._max_workers = count
        return self

    def with_database(self, path: str) -> 'CrawlerBuilder':
        """Set the database path."""
        self._db_path = path
        return self

    def with_debug(self, enabled: bool = True) -> 'CrawlerBuilder':
        """Enable or disable debug logging."""
        self._debug = enabled
        return self

    def build(self) -> 'CrawlerBuilder':
        """Build and initialize the crawler."""
        if not self._seed_ip or not self._username or not self._password:
            raise ValueError("Seed device configuration is incomplete")

        # Initialize database and add seed device
        db = Database(self._db_path)
        if not db.get_device_by_ip(self._seed_ip):
            db.add_device(self._seed_ip)

        # Create crawler instance
        self._crawler = NetworkCrawler(
            db=db,
            max_workers=self._max_workers,
            credentials={
                'username': self._username,
                'password': self._password
            },
            seed_ip=self._seed_ip
        )
        return self

    def start(self):
        """Start the crawler."""
        if not self._crawler:
            raise RuntimeError("Crawler not built. Call build() first.")
        self._crawler.start()

    def stop(self):
        """Stop the crawler."""
        if self._crawler:
            self._crawler.stop() 