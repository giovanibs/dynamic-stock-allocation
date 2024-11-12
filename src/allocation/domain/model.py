from dataclasses import dataclass
from datetime import date
from allocation.domain import events
from allocation.domain.exceptions import (
    CannotOverallocateError, InvalidSKU, LineIsNotAllocatedError, OutOfStock, SKUsDontMatchError)
from typing import List, Optional, Set


@dataclass(frozen=True)
class OrderLine:
    order_id: str
    sku: str
    qty: int


class Batch:

    def __init__(self, reference: str, sku: str, purchased_qty: int,
                 eta: Optional[date] = None ) -> None:
        self.reference = reference
        self.sku = sku
        self._purchased_qty = purchased_qty
        self.eta = eta
        self._allocations: Set[OrderLine] = set()


    def __gt__(self, other: 'Batch'):
        if self.eta is None:
            return False
        
        if other.eta is None:
            return True
        
        return self.eta > other.eta


    @property
    def allocated_qty(self):
        return sum(line.qty for line in self._allocations)
    

    @property
    def available_qty(self):
        return self._purchased_qty - self.allocated_qty
    

    @property
    def properties_dict(self):
        return {
        'reference': self.reference,
        'sku': self.sku,
        'purchased_qty': self._purchased_qty,
        'eta': self.eta,
        }

    
    def allocate(self, line: OrderLine) -> None:
        self._can_allocate(line)
        self._allocations.add(line)


    def _can_allocate(self, line: OrderLine) -> None:
        if self.sku != line.sku:
            raise SKUsDontMatchError()
        
        if self.available_qty - line.qty < 0:
            raise CannotOverallocateError()
    

    def can_allocate(self, line):
        try:
            self._can_allocate(line)
        except (SKUsDontMatchError, CannotOverallocateError):
            return False
        
        return True


    def deallocate(self, line: OrderLine) -> None:
        if line not in self._allocations:
            raise LineIsNotAllocatedError()
        
        self._allocations.remove(line)

    
    @property
    def allocations(self) -> List[OrderLine]:
        return list(self._allocations)


class Product:
    """Aggregate for batches."""

    def __init__(self, sku: str, batches: Optional[List[Batch]] = None) -> None:
        self._sku = sku
        self._batches = []
        self._events: List[events.Event] = []

        if batches:
            for batch in batches:
                self.validate_sku(batch.sku)
                self._batches.append(batch)


    @property
    def sku(self) -> str:
        return self._sku
    

    @property
    def batches(self) -> List[Batch]:
        return self._batches
    

    @property
    def events(self) -> List[events.Event]:
        return self._events
    

    def add_batch(self, reference: str, sku: str, purchased_qty: int,
                  eta: Optional[date] = None
    ):
        self.validate_sku(sku)
        self._batches.append(Batch(reference, sku, purchased_qty, eta))


    def allocate(self, order_id: str, sku: str, qty: int) -> str:

        self.validate_sku(sku)
        line = OrderLine(order_id, sku, qty)
        
        try:
            batch = self._get_suitable_batch_or_raise_error(line)
        except OutOfStock:
            self._events.append(events.OutOfStock(sku))
            return None
        
        batch.allocate(line)
        return batch.reference


    def _get_suitable_batch_or_raise_error(self, line):
        try:
            return next(batch 
                         for batch in sorted(self._batches)
                         if batch.can_allocate(line))
        except StopIteration:
            raise OutOfStock()


    def deallocate(self, order_id: str, sku: str, qty: int) -> str:
        
        self.validate_sku(sku)
        line = OrderLine(order_id, sku, qty)
        batch = self._get_batch_with_allocated_line_or_raise_error(line)
        batch.deallocate(line)
        return batch.reference


    def _get_batch_with_allocated_line_or_raise_error(self, line: OrderLine):
        try:
            return next(batch
                        for batch in self._batches
                        if line in batch.allocations)
        except StopIteration:
            raise LineIsNotAllocatedError()
        

    def validate_sku(self, sku):
        if sku != self._sku:
            raise InvalidSKU()
