import json
from loguru import logger

def get_url(index:str):
    try:
        logger.debug(f"Getting URL for index: {index}")
        with open('proxies_data.json','r') as f:
            urls=json.load(f)
        
        url = urls.get(index,'')
        if not url:
            logger.warning(f"No URL found for index: {index}")
        else:
            logger.debug(f"Retrieved URL for index {index}")
        return url
    except FileNotFoundError as e:
        logger.error(f"proxies_data.json file not found: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding proxies_data.json: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting URL: {e}")
        raise