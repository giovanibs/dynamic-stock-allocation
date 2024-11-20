import logging
import os
from typing import Callable, Dict, List, Type, Union
from allocation.config import get_logger
from allocation.domain import events, commands
from allocation.orchestration import handlers, query_handlers, uow


class MessageBus:
    
    Message = Union[commands.Command, events.Event]

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

    
    @classmethod
    def handle(cls, message: Message, uow: uow.AbstractUnitOfWork):
        logger = cls._get_logger()
        queue = [message]
        results = []
        
        while queue:
            message = queue.pop(0)

            if isinstance(message, commands.Command):
                results.append(cls.handle_command(message, queue, uow, logger))
            
            elif isinstance(message, events.Event):
                cls.handle_event(message, queue, uow, logger)
            
            else:
                raise TypeError(f'{message} is neither a command nor an event.')
            
        return results


    @classmethod
    def handle_command(cls,
                       command: commands.Command,
                       queue: List[Message],
                       uow: uow.AbstractUnitOfWork,
                       logger: logging.Logger
    ):
        logger.debug(f'Handling {command} with {cls.COMMAND_HANDLERS[type(command)]}')
        try:
            result = cls.COMMAND_HANDLERS[type(command)](command, uow)
        except Exception as e:
            logger.error(f'Exception while handling {command}: {type(e).__name__}')
            raise

        queue.extend(uow.collect_new_messages())
        return result


    @classmethod
    def handle_event(cls,
                     event: events.Event,
                     queue: List[Message],
                     uow: uow.AbstractUnitOfWork,
                     logger: logging.Logger
        ):
        results = []
        for handler in cls.EVENT_HANDLERS[type(event)]:
            logger.debug(f'Handling {event} with {handler}')
            try:
                results.append(handler(event, uow))
            except Exception as e:
                logger.error(f'Exception while handling {event} with {handler}: {type(e).__name__}')
                raise
            
            queue.extend(uow.collect_new_messages())
        
        return results


    @staticmethod
    def _get_logger():
        return get_logger()
