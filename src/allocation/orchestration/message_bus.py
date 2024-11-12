from typing import Callable, Dict, List, Type
from allocation.domain import events
from allocation.orchestration import services
from allocation.orchestration.uow import AbstractUnitOfWork


def handle(event: events.Event, uow: AbstractUnitOfWork):
    queue = [event]
    results = []
    while queue:
        event = queue.pop(0)
        for handler in HANDLERS[type(event)]:
            results.append(handler(event, uow))
            queue.extend(uow.collect_new_events())
    
    return results


HANDLERS: Dict[Type[events.Event], List[Callable]] = {
    events.OutOfStock: [services.log_warning],
    events.BatchCreated: [services.add_batch],
    events.AllocationRequired: [services.allocate],
}
