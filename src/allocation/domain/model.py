from dataclasses import dataclass, astuple
from datetime import date
from allocation.domain import commands, events
from allocation.domain.exceptions import (
    CannotOverallocateError, InvalidSKU, LineIsNotAllocatedError,
    OutOfStock, SKUsDontMatchError
)
from typing import List, Optional, Set, Union


@dataclass(frozen=True)
class OrderLine:
    order_id: str
    sku: str
    qty: int


class Batch:

    def __init__(self, ref: str, sku: str, qty: int,
                 eta: Optional[date] = None ) -> None:
        self.ref = ref
        self.sku = sku
        self._qty = qty
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
        return self._qty - self.allocated_qty
    

    @property
    def properties_dict(self):
        return {
        'ref': self.ref,
        'sku': self.sku,
        'qty': self._qty,
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


    def deallocate_one(self) -> OrderLine:
        if self._allocations:
            return self._allocations.pop()
        
        return None
        
    
    @property
    def allocations(self) -> List[OrderLine]:
        return list(self._allocations)
    

    @property
    def qty(self):
        return self._qty
    

    @qty.setter
    def qty(self, value):
        self._qty = value


class Product:
    """Aggregate for batches."""

    def __init__(self, sku: str, batches: Optional[List[Batch]] = None) -> None:
        self._sku = sku
        self._batches: List[Batch] = []
        self._messages: List[Union[commands.Command, events.Event]] = []

        if batches:
            for batch in batches:
                self.validate_sku(batch.sku)
                self._batches.append(batch)
                self._messages.append(events.BatchCreated(**batch.properties_dict))


    @property
    def sku(self) -> str:
        return self._sku
    

    @property
    def batches(self) -> List[Batch]:
        return self._batches
    

    @property
    def messages(self) -> List[Union[commands.Command, events.Event]]:
        return self._messages
    

    def add_batch(self, ref: str, sku: str, qty: int,
                  eta: Optional[date] = None
    ):
        self.validate_sku(sku)
        self._batches.append(Batch(ref, sku, qty, eta))
        self._messages.append(events.BatchCreated(ref, sku, qty, eta))


    def allocate(self, order_id: str, sku: str, qty: int) -> str:

        self.validate_sku(sku)
        line = OrderLine(order_id, sku, qty)
        
        try:
            batch = self._get_suitable_batch_or_raise_error(line)
        except OutOfStock:
            self._messages.append(events.OutOfStock(sku))
            raise
        
        batch.allocate(line)
        self._messages.append(events.LineAllocated(*astuple(line), batch.ref))
        return batch.ref


    def _get_suitable_batch_or_raise_error(self, line) -> Batch:
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
        self._messages.append(events.LineDeallocated(*astuple(line), batch.ref))
        return batch.ref


    def _get_batch_with_allocated_line_or_raise_error(self, line: OrderLine) -> Batch:
        try:
            return next(batch
                        for batch in self._batches
                        if line in batch.allocations)
        except StopIteration:
            raise LineIsNotAllocatedError()
        

    def validate_sku(self, sku):
        if sku != self._sku:
            raise InvalidSKU()
        

    def change_batch_quantity(self, ref: str, qty: int):
        batch = next(b for b in self.batches if b.ref == ref)
        batch.qty = qty

        while batch.allocated_qty > batch._qty:
            line = batch.deallocate_one()
            self._messages.append(events.LineDeallocated(*astuple(line), batch.ref))
            self._messages.append(commands.Reallocate(*astuple(line)))
