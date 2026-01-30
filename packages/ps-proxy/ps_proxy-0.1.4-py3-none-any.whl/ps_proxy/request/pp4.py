import requests
from io import StringIO
from .get import get_url
import pandas as pd
from loguru import logger

def get_proxies() -> list:
    try:
        logger.info("Fetching proxies from pp4 source")
        url = get_url('pp4')
        if not url:
            logger.error("URL for pp4 is empty")
            return []
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text))
        if not tables:
            logger.warning("No tables found in pp4 response")
            return []
        
        ip_table = tables[0]
        proxies_list = ip_table.apply(
        lambda row: {row['Type'].lower(): f"{row['IP Address']}:{row['Port']}"},
        axis=1
        ).tolist()
        logger.info(f"Successfully retrieved {len(proxies_list)} proxies from pp4")
        return proxies_list
    except requests.RequestException as e:
        logger.error(f"Request error in pp4: {e}")
        return []
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Error parsing pp4 response: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in pp4.get_proxies: {e}")
        return []

if __name__=='__main__':
    proxy_list = get_proxies()
    print(proxy_list)