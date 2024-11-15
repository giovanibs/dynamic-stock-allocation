from dataclasses import dataclass
from datetime import date
from typing import Optional


class Command:
    pass


@dataclass(frozen=True)
class CreateBatch(Command):
    ref: str
    sku: str
    qty: int
    eta: Optional[date] = None


@dataclass(frozen=True)
class Allocate(Command):
    order_id: str
    sku: str
    qty: int


@dataclass(frozen=True)
class Deallocate(Command):
    order_id: str
    sku: str
    qty: int


@dataclass(frozen=True)
class ChangeBatchQuantity(Command):
    ref: str
    qty: int


@dataclass(frozen=True)
class Reallocate(Command):
    order_id: str
    sku: str
    qty: int
