import json
from loguru import logger
import os
from .proxy_data import proxy_data

def get_url(index:str):
    try:
        url = proxy_data.get(index,"")
        return url
    except Exception as e:
        logger.error(f'No url found for the index {index=}')
        return ""