import json
from loguru import logger
import os
from pathlib import Path

def get_url(index:str):
    try:
        logger.debug(f"Getting URL for index: {index}")
        module_dir = Path(__file__).parent.parent
        json_path = module_dir / 'proxies_data.json'
        
        with open(json_path, 'r') as f:
            urls = json.load(f)
        
        url = urls.get(index, '')
        if not url:
            logger.warning(f"No URL found for index: {index}")
        else:
            logger.debug(f"Retrieved URL for index {index}")
        return url
    except FileNotFoundError as e:
        logger.error(f"proxies_data.json file not found at {json_path}: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding proxies_data.json: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting URL: {e}")
        raise