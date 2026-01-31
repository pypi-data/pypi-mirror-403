import logging

from yi_config_starter.config_starter import ApplicationConfiguration

logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "0.1.3"
__all__ = ["ApplicationConfiguration"]
