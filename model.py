from dataclasses import dataclass
from datetime import date
from exceptions import CannotOverallocateError, LineIsNotAllocatedError, SKUsDontMatchError
from typing import List


@dataclass(frozen=True)
class OrderLine:
    ref: str
    sku: str
    qty: int


class Batch:

    def __init__(
            self,
            ref: str,
            sku: str,
            available_qty: int,
            eta: date ) -> None:
        
        self.ref = ref
        self.sku = sku
        self.available_qty = available_qty
        self.eta = eta
        self.order_lines: List[OrderLine] = []

    
    def allocate(self, order_line: OrderLine) -> None:
        self._can_allocate(order_line)
        self.available_qty -= order_line.qty
        self.order_lines.append(order_line)


    def _can_allocate(self, order_line: OrderLine) -> None:
        if self.sku != order_line.sku:
            raise SKUsDontMatchError()
        
        if self.available_qty - order_line.qty < 0:
            raise CannotOverallocateError()
        

    def deallocate(self, order_line: OrderLine) -> None:
        if order_line not in self.order_lines:
            raise LineIsNotAllocatedError()
        
        self.available_qty += order_line.qty
        self.order_lines.remove(order_line)
