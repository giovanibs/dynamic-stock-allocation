"""Events handler"""

import os
from typing import Callable, Dict, List, Type
from allocation.domain import events
import logging


def handle(event: events.Event):
    for handler in HANDLERS[type(event)]:
        handler(event)


def log_warning(event: events.OutOfStock):
    logger = logging.getLogger(__name__)

    if logger.hasHandlers():
        logger.handlers.clear()

    filename = os.path.join(os.getcwd(), 'logs.log')
    file_handler = logging.FileHandler(filename, mode='w')
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    logger.warning(f"'{event.sku}' is out of stock!")


HANDLERS: Dict[Type[events.Event], List[Callable]] = {
    events.OutOfStock: [log_warning] 
}
