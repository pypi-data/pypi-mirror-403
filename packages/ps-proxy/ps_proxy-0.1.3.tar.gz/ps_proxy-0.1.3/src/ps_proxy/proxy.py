from .request.pp1 import get_proxies as gp1
from .request.pp2 import get_proxies as gp2
from .request.pp3 import get_proxies as gp3
from .request.pp4 import get_proxies as gp4

from .database.crud import Database

import random
import ast
from loguru import logger


class ProxyManager:
    
    def __init__(self):
        try:
            logger.info("Initializing ProxyManager")
            self.database = Database()
            self.proxy_sources = [gp1, gp2, gp3, gp4]
            logger.debug(f"ProxyManager initialized with {len(self.proxy_sources)} proxy sources")
        except Exception as e:
            logger.error(f"Error initializing ProxyManager: {e}")
            raise
    
    def gather_proxies_from_sources(self):
        try:
            logger.info("Starting to gather proxies from sources")
            gathered_proxies = []
            for idx, source in enumerate(self.proxy_sources):
                try:
                    proxies = source()
                    gathered_proxies.extend(proxies)
                    logger.debug(f"Source {idx + 1} returned {len(proxies)} proxies")
                except Exception as e:
                    logger.warning(f"Error gathering from source {idx + 1}: {e}")
                    continue
            logger.info(f"Total proxies gathered: {len(gathered_proxies)}")
            return gathered_proxies
        except Exception as e:
            logger.error(f"Error gathering proxies from sources: {e}")
            raise
    
    def initialize_proxies(self):
        try:
            logger.info("Initializing proxies")
            available_proxies = self.database.read_proxy()
            logger.debug(f"Retrieved {len(available_proxies)} proxies from database")
            
            if len(available_proxies) == 0:
                logger.info("No proxies in database, gathering from sources")
                proxies = self.gather_proxies_from_sources()
                for proxy in proxies:
                    try:
                        self.database.create_proxy(proxy)
                    except Exception as e:
                        logger.warning(f"Error creating proxy: {e}")
                        continue
                available_proxies = self.database.read_proxy()
                logger.info(f"Stored {len(available_proxies)} proxies in database")
            
            return available_proxies
        except Exception as e:
            logger.error(f"Error initializing proxies: {e}")
            raise
    
    def get_random_proxy(self):
        try:
            logger.info("Getting random proxy")
            available_proxies = self.initialize_proxies()
            
            if not available_proxies:
                logger.error("No proxies available")
                raise ValueError("No proxies available")
            
            random_proxy_class = random.choice(available_proxies)
            self.database.delete_proxy(id=random_proxy_class.id)
            logger.debug(f"Selected and deleted proxy with id {random_proxy_class.id}")
            
            proxy_dict = ast.literal_eval(random_proxy_class.proxy)
            logger.info(f"Returning proxy: {proxy_dict}")
            return proxy_dict
        except ValueError as e:
            logger.error(f"ValueError in get_random_proxy: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting random proxy: {e}")
            raise


def main():
    try:
        logger.info("Starting main function")
        proxy_manager = ProxyManager()
        
        available_proxies = proxy_manager.initialize_proxies()
        logger.info(f"Main function completed with {len(available_proxies)} available proxies")
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise
    print(f"Available proxies: {len(available_proxies)}")
    
    random_proxy = proxy_manager.get_random_proxy()
    print(f"Selected proxy: {random_proxy}")


if __name__ == "__main__":
    main()




