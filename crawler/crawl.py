import logging
from typing import Optional
from .crawler import Crawler

class CrawlerBuilder:
    def __init__(self):
        self._seed_hostname: Optional[str] = None
        self._username: Optional[str] = None
        self._password: Optional[str] = None
        self._db_path: str = 'network_crawl.db'
        self._workers: int = 4
        self._max_retries: int = 3
        self._logger = logging.getLogger(__name__)

    def with_seed_device(self, hostname: str, username: str, password: str) -> 'CrawlerBuilder':
        self._seed_hostname = hostname
        self._username = username
        self._password = password
        return self

    def with_db_path(self, db_path: str) -> 'CrawlerBuilder':
        self._db_path = db_path
        return self

    def with_workers(self, workers: int) -> 'CrawlerBuilder':
        self._workers = workers
        return self

    def with_max_retries(self, max_retries: int) -> 'CrawlerBuilder':
        self._max_retries = max_retries
        return self

    def build(self) -> Crawler:
        if not all([self._seed_hostname, self._username, self._password]):
            raise ValueError("Seed device information is incomplete. Please provide all required fields.")

        crawler = Crawler(
            db_path=self._db_path,
            max_retries=self._max_retries,
            username=self._username,
            password=self._password
        )
        
        crawler.add_seed_device(
            hostname=self._seed_hostname,
            username=self._username,
            password=self._password
        )
        
        return crawler

    def start(self) -> None:
        crawler = self.build()
        self._logger.info("Starting crawler...")
        crawler.start(num_workers=self._workers)
        
        try:
            while True:
                pass
        except KeyboardInterrupt:
            self._logger.info("Received shutdown signal")
        finally:
            crawler.stop()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Network Discovery Crawler')
    parser.add_argument('--seed-hostname', required=True, help='Hostname of seed device')
    parser.add_argument('--username', required=True, help='SSH username')
    parser.add_argument('--password', required=True, help='SSH password')
    parser.add_argument('--db-path', default='network_crawl.db', help='Path to SQLite database')
    parser.add_argument('--workers', type=int, default=4, help='Number of worker threads')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum retry attempts per device')
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        builder = CrawlerBuilder()
        builder.with_seed_device(
            hostname=args.seed_hostname,
            username=args.username,
            password=args.password
        ).with_db_path(args.db_path)\
         .with_workers(args.workers)\
         .with_max_retries(args.max_retries)\
         .start()
            
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        raise

if __name__ == '__main__':
    main() 