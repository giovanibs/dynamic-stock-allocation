from typing import Callable, Dict, List, Type, Union
from allocation.config import get_logger
from allocation.domain import events, commands
from allocation.domain.exceptions import OutOfStock
from allocation.orchestration.uow import AbstractUnitOfWork


class MessageBus:
    
    Message = Union[commands.Command, events.Event]

    def __init__(
            self,
            uow: AbstractUnitOfWork,
            command_handlers: Dict[Type[commands.Command], Callable],
            event_handlers: Dict[Type[events.Event], List[Callable]]
    ) -> None:
        
        self._uow = uow
        self._command_handlers = command_handlers
        self._event_handlers = event_handlers
        self._logger = get_logger()

    
    def handle(self, message: Message):
        self._queue = [message]
        results = []
        
        while self._queue:
            message = self._queue.pop(0)

            if isinstance(message, commands.Command):
                results.append(self.handle_command(message))
            
            elif isinstance(message, events.Event):
                self.handle_event(message)
            
            else:
                raise TypeError(f'{message} is neither a command nor an event.')
            
        return results


    def handle_command(self, command: commands.Command):
        command_handler = self._command_handlers[type(command)]
        self.log_debug(command, command_handler)
        try:
            result = command_handler(command)
        
        except OutOfStock:
            # Collect OutOfStock event from UoW, process remaining queue events,
            # then re-raise OutOfStock exception
            self._queue.extend(self._uow.collect_new_messages())
            for event in self._queue:
                self.handle_event(event)
            raise
        except Exception as e:
            self.log_error(command, command_handler, e)
            raise

        self._queue.extend(self._uow.collect_new_messages())
        return result


    def handle_event(self, event: events.Event):
        for handler in self._event_handlers[type(event)]:
            self.log_debug(event, handler)
            try:
                handler(event)
            except Exception as e:
                self.log_error(event, handler, e)
                raise
            
            self._queue.extend(self._uow.collect_new_messages())
    

    def log_debug(self, message: Message, handler):
        self._logger.debug(f'Handling {message} with {handler}')


    def log_error(self, message: Message, handler, err: Exception):
        self._logger.error(
            f'Exception handling {message} with {handler}: ' \
            f'{type(err).__name__}'
        )

