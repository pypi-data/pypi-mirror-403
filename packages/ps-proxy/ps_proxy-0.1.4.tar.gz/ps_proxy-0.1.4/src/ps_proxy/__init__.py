from loguru import logger

__version__ = "0.1.0"
__author__ = "Praful Sapkota"

logger.debug(f"ps_proxy v{__version__} initialized")

# Export main classes
from .proxy import ProxyManager

__all__ = ["ProxyManager", "__version__"]