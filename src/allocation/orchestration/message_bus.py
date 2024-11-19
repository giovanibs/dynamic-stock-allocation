import logging
import os
from typing import Callable, Dict, List, Type, Union
from allocation.domain import events, commands
from allocation.orchestration import handlers, uow


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
            handlers.add_batch_to_query_repository,
        ],
        events.BatchQuantityChanged : [
            handlers.publish_event,
            handlers.update_batch_quantity_in_query_repository,
        ],
        events.LineAllocated: [
            handlers.publish_event,
            handlers.add_allocation_to_query_repository,
            handlers.add_order_allocation_to_query_repository,
        ],
        events.LineDeallocated : [
            handlers.publish_event,
            handlers.remove_allocation_from_query_repository,
            handlers.remove_allocations_for_order_from_query_repository,
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
        logger = logging.getLogger(__name__)

        if logger.hasHandlers():
            logger.handlers.clear()

        filename = os.path.join(os.getcwd(), 'logs.log')
        file_handler = logging.FileHandler(filename, mode='a')
        formatter = logging.Formatter('%(asctime)s--%(name)s--%(levelname)s: %(message)s',
                                  "%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)
        return logger
