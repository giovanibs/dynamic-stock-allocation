from dataclasses import dataclass
from datetime import date
from src.allocation.domain.exceptions import (
    CannotOverallocateError, LineIsNotAllocatedError, OutOfStock, SKUsDontMatchError)
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


def allocate(line: OrderLine, batches: List[Batch]) -> str:
    """Domain service"""
    try:
        batch = next(batch for batch in sorted(batches) if batch.can_allocate(line))
    except StopIteration:
        raise OutOfStock()
    
    batch.allocate(line)
    return batch.ref
