from abc import ABC, abstractmethod
from allocation.adapters.repository import (
    AbstractRepository, DjangoProductRepository, DjangoRepository, AbstractProductRepository)
from django.db import transaction


class AbstractUnitOfWork(ABC):
    batches: AbstractRepository


    def __exit__(self, *args):
        self.rollback()

    
    def __enter__(self):
        return self


    @abstractmethod
    def commit(self):
        raise NotImplementedError()


    @abstractmethod
    def rollback(self):
        raise NotImplementedError()


class AbstractProductUnitOfWork(ABC):
    products: AbstractProductRepository


    def __exit__(self, *args):
        self.rollback()

    
    def __enter__(self):
        return self


    @abstractmethod
    def commit(self):
        raise NotImplementedError()


    @abstractmethod
    def rollback(self):
        raise NotImplementedError()


class DjangoUoW(AbstractUnitOfWork):

    def __enter__(self):
        self.batches = DjangoRepository()
        transaction.set_autocommit(False)
        return super().__enter__()
    

    def __exit__(self, *args):
        super().__exit__(*args)
        transaction.set_autocommit(True)


    def commit(self):
        for batch in self.batches.seen:
            self.batches.update(batch)
        transaction.commit()


    def rollback(self):
        transaction.rollback()


class DjangoProductUoW(AbstractProductUnitOfWork):

    def __enter__(self):
        self._products = DjangoProductRepository()
        transaction.set_autocommit(False)
        return super().__enter__()
    

    @property
    def products(self):
        return self._products
    

    def __exit__(self, *args):
        super().__exit__(*args)
        transaction.set_autocommit(True)


    def commit(self):
        for batch in self.products.seen:
            self.products.update(batch)
        transaction.commit()


    def rollback(self):
        transaction.rollback()
