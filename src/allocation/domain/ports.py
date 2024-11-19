from abc import ABC, abstractmethod
from typing import List, Set, Tuple

from allocation.domain.model import Batch, Product


class AbstractWriteRepository(ABC):

    def __init__(self) -> None:
        self._seen: Set[Product] = set()


    @property
    def seen(self):
        return self._seen


    @abstractmethod
    def add(self, product: Product) -> None:
        self._seen.add(product)


    def get(self, sku) -> Product:
        # first check if product is already in self._seen to prevent overwriting
        # uncommited changes by refetching it from the DB
        product = next((p for p in self._seen if p.sku == sku), None)
        if product is None:
            product = self._get(sku)
            self._seen.add(product)
        return product
    

    @abstractmethod
    def _get(self, sku) -> Product:
        raise NotImplementedError()
    

    @abstractmethod
    def update(self, product: Product) -> None:
        raise NotImplementedError()
    

    @abstractmethod
    def list(self) -> List[Product]:
        raise NotImplementedError()
    

    def get_by_batch_ref(self, ref: str):
        # first check if product is already in self._seen to prevent overwriting
        # uncommited changes by refetching it from the DB
        product_in_seen = next(
            (p for p in self.seen for b in p.batches if b.ref == ref),
            None
        )
        if product_in_seen is not None:
            return product_in_seen
        
        product = self._get_by_batch_ref(ref)
        
        if product is None:
            return None
        
        self._seen.add(product)
        return product
    

    @abstractmethod
    def _get_by_batch_ref(self, ref):
        raise NotImplemented


class AbstractQueryRepository(ABC):

    @abstractmethod
    def get_batch(self, ref: str) -> Batch:
        """"Returns a batch for a given reference"""
        raise NotImplementedError
    

    def allocation_for_line(self, order_id: str, sku: str) -> str:
        """Returns the batch reference for a given order line."""
        raise NotImplementedError
