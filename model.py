from dataclasses import dataclass
from datetime import date
from exceptions import CannotOverallocateError, SKUsDontMatchError


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

    
    def allocate(self, order_line: OrderLine):
        if self.sku != order_line.sku:
            raise SKUsDontMatchError()
        
        if self.available_qty - order_line.qty < 0:
            raise CannotOverallocateError()
        
        self.available_qty -= order_line.qty
