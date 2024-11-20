from abc import ABC, abstractmethod
from typing import Optional
from allocation.adapters.redis_query_repository import RedisQueryRepository
from allocation.config import get_redis_config
from allocation.domain.ports import AbstractQueryRepository, AbstractWriteRepository
from allocation.adapters.django_repository import DjangoRepository
from django.db import transaction


class AbstractUnitOfWork(ABC):
    products: AbstractWriteRepository
    querier: AbstractQueryRepository


    def __exit__(self, *args):
        self.rollback()

    
    def __enter__(self):
        return self


    def commit(self):
        self._commit()


    def collect_new_messages(self):
        for product in self.products.seen:
            while product.messages:
                yield product.messages.pop(0)


    @abstractmethod
    def _commit(self):
        raise NotImplementedError()


    @abstractmethod
    def rollback(self):
        raise NotImplementedError()


class DjangoUoW(AbstractUnitOfWork):

    def __init__(self, querier: Optional[AbstractQueryRepository] = None) -> None:
        self._products = DjangoRepository()
        self._querier = querier if querier else RedisQueryRepository(*get_redis_config())

    
    def __enter__(self):
        transaction.set_autocommit(False)
        return super().__enter__()
    

    @property
    def products(self) -> DjangoRepository:
        return self._products
    
    
    @property
    def querier(self) -> RedisQueryRepository:
        return self._querier
    

    def __exit__(self, *args):
        super().__exit__(*args)
        transaction.set_autocommit(True)


    def _commit(self):
        for product in self.products.seen:
            self.products.update(product)
        transaction.commit()


    def rollback(self):
        transaction.rollback()
