from .request.pp1 import get_proxies as gp1
from .request.pp2 import get_proxies as gp2
from .request.pp3 import get_proxies as gp3
from .request.pp4 import get_proxies as gp4

from .database.crud import Database

import random
import ast
from loguru import logger
import requests


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


    def _format_proxy(self, proxy: dict) -> dict:
        if not proxy or not isinstance(proxy, dict):
            return {}

        proto, addr = next(iter(proxy.items()))

        if proto in ("http", "https"):
            url = addr if "://" in addr else f"http://{addr}"
            return {"http": url, "https": url}

        if proto in ("socks4", "socks5"):
            url = addr if "://" in addr else f"{proto}://{addr}"
            return {"http": url, "https": url}

        return proxy

    def _get_direct_ip(self) -> str:
        """Get your direct public IP without any proxy."""
        return requests.get("https://api.ipify.org", timeout=10).text.strip()

    def _check_http(self, proxy: dict) -> bool:

        try:
            formatted = self._format_proxy(proxy)
            r = requests.get("http://httpbin.org/ip", timeout=10, proxies=formatted)
            ok = r.status_code == 200
            if not ok:
                logger.warning(f"HTTP test failed with status {r.status_code} for proxy={proxy}")
            return ok
        except Exception as e:
            logger.warning(f"HTTP test error for proxy={proxy}: {e}")
            return False

    def _check_https_and_ip_change(self, proxy: dict) -> bool:

        try:
            formatted = self._format_proxy(proxy)

            direct_ip = self._get_direct_ip()
            proxy_ip = requests.get("https://api.ipify.org", timeout=10, proxies=formatted).text.strip()

            logger.info(f"Direct IP: {direct_ip} | Proxy IP: {proxy_ip}")

            return proxy_ip != "" and proxy_ip != direct_ip
        except Exception as e:
            logger.warning(f"HTTPS/IP check error for proxy={proxy}: {e}")
            return False

    def _is_proxy_valid(self, proxy: dict, require_https: bool = True, require_ip_change: bool = True) -> bool:

        if not self._check_http(proxy):
            return False

        if not require_https:
            return True

        if require_ip_change:
            return self._check_https_and_ip_change(proxy)

        try:
            formatted = self._format_proxy(proxy)
            r = requests.get("https://api.ipify.org", timeout=10, proxies=formatted)
            return r.status_code == 200
        except Exception:
            return False


    def get_random_proxy(self, check: bool = False, require_https: bool = False, require_ip_change: bool = False):
  
        try:
            logger.info("Getting random proxy")
            available_proxies = self.initialize_proxies()

            if not available_proxies:
                logger.error("No proxies available")
                raise ValueError("No proxies available")

            for _ in range(len(available_proxies)):
                random_proxy_class = random.choice(available_proxies)
                proxy_dict = ast.literal_eval(random_proxy_class.proxy)

                if check:
                    valid = self._is_proxy_valid(
                        proxy_dict,
                        require_https=require_https,
                        require_ip_change=require_ip_change,
                    )
                    if not valid:
                        self.database.delete_proxy(id=random_proxy_class.id)
                        logger.warning(f"Proxy {proxy_dict} failed validation, deleted")
                        available_proxies = self.database.read_proxy()
                        if not available_proxies:
                            break
                        continue

                self.database.delete_proxy(id=random_proxy_class.id)
                logger.info(f"Returning proxy: {proxy_dict}")
                return self._format_proxy(proxy_dict)

            raise ValueError("No valid proxies available")
        except Exception as e:
            logger.error(f"Error getting random proxy: {e}")
            raise


def main():
    try:
        logger.info("Starting main function")
        proxy_manager = ProxyManager()

        available_proxies = proxy_manager.initialize_proxies()
        logger.info(f"Main function completed with {len(available_proxies)} available proxies")
        print(f"Available proxies: {len(available_proxies)}")

        random_proxy = proxy_manager.get_random_proxy()
        print(f"Selected proxy: {random_proxy}")


    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise


if __name__ == "__main__":
    main()
