from abc import ABC, abstractmethod
from allocation.adapters.repository import (
    DjangoRepository, AbstractRepository)
from django.db import transaction
from allocation.orchestration import message_bus


class AbstractUnitOfWork(ABC):
    products: AbstractRepository
    event_handler = staticmethod(message_bus.handle)


    def __exit__(self, *args):
        self.rollback()

    
    def __enter__(self):
        return self


    def commit(self):
        self._commit()
        self._publish_events()


    def _publish_events(self):
        for product in self.products.seen:
            while product.events:
                event = product.events.pop(0)
                self.event_handler(event)


    @abstractmethod
    def _commit(self):
        raise NotImplementedError()


    @abstractmethod
    def rollback(self):
        raise NotImplementedError()


class DjangoProductUoW(AbstractUnitOfWork):

    def __enter__(self):
        self._products = DjangoRepository()
        transaction.set_autocommit(False)
        return super().__enter__()
    

    @property
    def products(self):
        return self._products
    

    def __exit__(self, *args):
        super().__exit__(*args)
        transaction.set_autocommit(True)


    def _commit(self):
        for product in self.products.seen:
            self.products.update(product)
        transaction.commit()


    def rollback(self):
        transaction.rollback()
