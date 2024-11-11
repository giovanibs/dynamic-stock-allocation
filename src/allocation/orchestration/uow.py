from abc import ABC, abstractmethod
from allocation.adapters.repository import (
    DjangoProductRepository, AbstractProductRepository)
from django.db import transaction


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
        for product in self.products.seen:
            self.products.update(product)
        transaction.commit()


    def rollback(self):
        transaction.rollback()
