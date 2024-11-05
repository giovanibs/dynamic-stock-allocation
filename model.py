from dataclasses import dataclass
from datetime import date


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
        self.available_qty -= order_line.qty
