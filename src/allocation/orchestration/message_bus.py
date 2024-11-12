from typing import Callable, Dict, List, Type
from allocation.domain import events
from allocation.orchestration import handlers, uow


def handle(event: events.Event, uow: uow.AbstractUnitOfWork):
    queue = [event]
    results = []
    while queue:
        event = queue.pop(0)
        for handler in HANDLERS[type(event)]:
            results.append(handler(event, uow))
            queue.extend(uow.collect_new_events())
    
    return results


HANDLERS: Dict[Type[events.Event], List[Callable]] = {
    events.OutOfStock: [handlers.log_warning],
    events.BatchCreated: [handlers.add_batch],
    events.AllocationRequired: [handlers.allocate],
    events.DeallocationRequired: [handlers.deallocate],
}
