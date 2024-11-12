"""Events handler"""

from typing import Callable, Dict, List, Type
from allocation.domain import events


def handle(event: events.Event):
    for handler in HANDLERS[type(event)]:
        handler(event)


def do_nothing(event: events.OutOfStock):
    pass


HANDLERS: Dict[Type[events.Event], List[Callable]] = {
    events.OutOfStock: [do_nothing] 
}
