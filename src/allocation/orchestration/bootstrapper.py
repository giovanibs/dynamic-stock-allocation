import inspect
from typing import Callable, Dict, List, Type
from allocation.adapters.redis_publisher import RedisEventPublisher
from allocation.adapters.redis_query_repository import RedisQueryRepository
from allocation.config import get_redis_config
from allocation.domain import commands, events, queries
from allocation.domain.ports import AbstractPublisher, AbstractQueryRepository
from allocation.orchestration import handlers, query_handlers
from allocation.orchestration.message_bus import MessageBus
from allocation.orchestration.uow import AbstractUnitOfWork, DjangoUoW


COMMAND_HANDLERS: Dict[Type[commands.Command], Callable] = {
        commands.CreateBatch            : handlers.add_batch,
        commands.Allocate               : handlers.allocate,
        commands.Deallocate             : handlers.deallocate,
        commands.ChangeBatchQuantity    : handlers.change_batch_quantity,
        commands.Reallocate             : handlers.reallocate,
    }


EVENT_HANDLERS: Dict[Type[events.Event], List[Callable]] = {
        events.BatchCreated : [
            handlers.publish_event,
            query_handlers.add_batch,
        ],
        events.BatchQuantityChanged : [
            handlers.publish_event,
            query_handlers.update_batch_quantity,
        ],
        events.LineAllocated: [
            handlers.publish_event,
            query_handlers.add_allocation,
            query_handlers.add_order_allocation,
        ],
        events.LineDeallocated : [
            handlers.publish_event,
            query_handlers.remove_allocation,
            query_handlers.remove_allocations_for_order,
        ],
        events.OutOfStock : [handlers.publish_event],
    }


QUERY_HANDLERS: Dict[Type[queries.Query], Callable] = {
    queries.BatchByRef          : query_handlers.get_batch,
    queries.AllocationForLine   : query_handlers.get_allocation_for_line,
    queries.AllocationsForOrder : query_handlers.get_allocations_for_order,
}


def bootstrap(
        uow: AbstractUnitOfWork = None,
        publisher: AbstractPublisher = None,
        query_repository: AbstractQueryRepository = None
) -> MessageBus:
    """
    Initializes and returns a MessageBus instance with all dependencies injected
    for itself, as well as its command and event handlers, using the specified or 
    default dependencies (see code for details).
    """
    
    redis_host, redis_port = get_redis_config()

    dependencies = {
        'uow': uow if uow is not None else DjangoUoW(),
        
        'publisher': publisher if publisher is not None
                     else RedisEventPublisher(redis_host, redis_port),
        
        'query_repository': query_repository if query_repository is not None
                            else RedisQueryRepository(redis_host, redis_port)
    }

    injected_command_handlers = {
        command: inject_dependencies(dependencies, command_handler)
        for command, command_handler in COMMAND_HANDLERS.items()
    }

    injected_event_handlers = {
        
        event: [
            inject_dependencies(dependencies, event_handler)
            for event_handler in event_handlers
        ]
        for event, event_handlers in EVENT_HANDLERS.items()
    }

    injected_query_handlers = {
        query: inject_dependencies(dependencies, query_handler)
        for query, query_handler in QUERY_HANDLERS.items()
    }

    return MessageBus(
        uow = dependencies['uow'],
        command_handlers = injected_command_handlers,
        event_handlers = injected_event_handlers,
        query_handlers = injected_query_handlers,
    )


def inject_dependencies(dependencies, handler):

    handler_parameters = inspect.signature(handler).parameters

    dependencies_to_inject = {
        name: dependency
        for name, dependency in dependencies.items()
        if name in handler_parameters
    }
    
    return lambda message: handler(message, **dependencies_to_inject)
