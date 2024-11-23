from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional, Set

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
        raise NotImplementedError()


class AbstractQueryRepository(ABC):

    @abstractmethod
    def add_batch(self, ref: str, sku: str, qty: int, eta: Optional[date] = None):
        raise NotImplementedError


    @abstractmethod
    def get_batch(self, ref: str) -> Batch:
        """"Returns a batch for a given reference"""
        raise NotImplementedError
    
    
    @abstractmethod
    def update_batch_quantity(self, ref: str, qty: int):
        raise NotImplementedError


    @abstractmethod
    def add_allocation_for_line(self, order_id, sku, batch_ref):
        raise NotImplementedError


    @abstractmethod
    def get_allocation_for_line(self, order_id: str, sku: str) -> str:
        """Returns the batch reference for a given order line."""
        raise NotImplementedError


    @abstractmethod
    def remove_allocation_for_line(self, order_id, sku):
        raise NotImplementedError


    @abstractmethod
    def add_allocation_for_order(self, order_id, sku, batch_ref):
        raise NotImplementedError


    @abstractmethod
    def get_allocations_for_order(self, order_id: str):
        """Returns a list of mappings `sku: batch_ref` for a given `order_id`"""
        raise NotImplementedError


    @abstractmethod
    def remove_allocation_for_order(self, order_id, sku):
        raise NotImplementedError


class AbstractPublisher(ABC):

    @abstractmethod
    def publish_event():
        raise NotImplementedError
