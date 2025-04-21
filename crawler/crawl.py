import logging
import argparse
from typing import Optional

from .builder import CrawlerBuilder

def setup_logging(level: int = logging.INFO):
    """Configure logging for the crawler."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    parser = argparse.ArgumentParser(description='Network Discovery Crawler')
    parser.add_argument('--seed', required=True, help='Seed device IP address')
    parser.add_argument('--username', required=True, help='SSH username')
    parser.add_argument('--password', required=True, help='SSH password')
    parser.add_argument('--workers', type=int, default=5, help='Number of worker threads')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    # Setup logging
    setup_logging(logging.DEBUG if args.debug else logging.INFO)
    logger = logging.getLogger("crawler")

    try:
        # Build and start crawler
        crawler = (
            CrawlerBuilder()
            .with_seed_device(args.seed, args.username, args.password)
            .with_workers(args.workers)
            .with_debug(args.debug)
            .build()
        )
        
        logger.info("Starting network crawler...")
        try:
            crawler.start()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal, stopping crawler...")
            crawler.stop()
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
