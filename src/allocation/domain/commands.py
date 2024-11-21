from dataclasses import dataclass
from datetime import date
from typing import Optional

from allocation.domain.validators import ValidQtyAndETAMixin, ValidQtyMixin


class Command:
    pass


@dataclass(frozen=True)
class CreateBatch(Command, ValidQtyAndETAMixin):
    ref: str
    sku: str
    qty: int
    eta: Optional[date] = None


@dataclass(frozen=True)
class Allocate(Command, ValidQtyMixin):
    order_id: str
    sku: str
    qty: int


@dataclass(frozen=True)
class Deallocate(Command, ValidQtyMixin):
    order_id: str
    sku: str
    qty: int


@dataclass(frozen=True)
class ChangeBatchQuantity(Command, ValidQtyMixin):
    ref: str
    qty: int


@dataclass(frozen=True)
class Reallocate(Command, ValidQtyMixin):
    order_id: str
    sku: str
    qty: int
