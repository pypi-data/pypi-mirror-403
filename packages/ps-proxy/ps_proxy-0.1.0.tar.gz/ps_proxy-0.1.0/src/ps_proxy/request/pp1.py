import requests
from .get import get_url
from loguru import logger

def get_proxies():
    try:
        logger.info("Fetching proxies from pp1 source")
        url = get_url('pp1')
        if not url:
            logger.error("URL for pp1 is empty")
            return []
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        response_body = response.json()
        all_proxy_list = response_body.get('data', [])
        
        proxy_list = [{proxy.get('protocols')[0].lower():f"{proxy.get('ip')}:{proxy.get('port')}"} for proxy in all_proxy_list]
        logger.info(f"Successfully retrieved {len(proxy_list)} proxies from pp1")
        return proxy_list
    except requests.RequestException as e:
        logger.error(f"Request error in pp1: {e}")
        return []
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Error parsing pp1 response: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in pp1.get_proxies: {e}")
        return []
   

if __name__=="__main__":
    get_proxies()