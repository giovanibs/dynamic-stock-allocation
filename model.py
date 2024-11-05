from dataclasses import dataclass
from datetime import date
from exceptions import CannotOverallocateError, LineIsNotAllocatedError, SKUsDontMatchError
from typing import Set


@dataclass(frozen=True)
class OrderLine:
    ref: str
    sku: str
    qty: int


class Batch:

    def __init__(self, ref: str, sku: str, qty: int, eta: date ) -> None:
        self.ref = ref
        self.sku = sku
        self._purchased_qty = qty
        self.eta = eta
        self._allocations: Set[OrderLine] = set()


    @property
    def allocated_qty(self):
        return sum(line.qty for line in self._allocations)
    

    @property
    def available_qty(self):
        return self._purchased_qty - self.allocated_qty

    
    def allocate(self, order_line: OrderLine) -> None:
        self._can_allocate(order_line)
        self._allocations.add(order_line)


    def _can_allocate(self, order_line: OrderLine) -> None:
        if self.sku != order_line.sku:
            raise SKUsDontMatchError()
        
        if self.available_qty - order_line.qty < 0:
            raise CannotOverallocateError()
        

    def deallocate(self, order_line: OrderLine) -> None:
        if order_line not in self._allocations:
            raise LineIsNotAllocatedError()
        
        self._allocations.remove(order_line)
