import argparse
import logging
from typing import Optional
from .crawler import Crawler

def parse_args():
    parser = argparse.ArgumentParser(description='Network Discovery Crawler')
    parser.add_argument('--seed-ip', required=True, help='IP address of seed device')
    parser.add_argument('--seed-hostname', required=True, help='Hostname of seed device')
    parser.add_argument('--username', required=True, help='SSH username')
    parser.add_argument('--password', required=True, help='SSH password')
    parser.add_argument('--db-path', default='network_crawl.db', help='Path to SQLite database')
    parser.add_argument('--workers', type=int, default=4, help='Number of worker threads')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum retry attempts per device')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize crawler
        crawler = Crawler(
            db_path=args.db_path,
            max_retries=args.max_retries
        )
        
        # Add seed device
        crawler.add_seed_device(
            hostname=args.seed_hostname,
            ip=args.seed_ip,
            username=args.username,
            password=args.password
        )
        
        # Start crawling
        logger.info("Starting crawler...")
        crawler.start(num_workers=args.workers)
        
        # Keep main thread alive
        try:
            while True:
                pass
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            crawler.stop()
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == '__main__':
    main() 