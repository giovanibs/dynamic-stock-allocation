from dataclasses import dataclass
from datetime import date
from typing import Optional


class Event:
    pass


@dataclass(frozen=True)
class OutOfStock(Event):
    sku: str


@dataclass(frozen=True)
class BatchCreated(Event):
    ref: str
    sku: str
    qty: int
    eta: Optional[date] = None


@dataclass(frozen=True)
class BatchQuantityChanged(Event):
    ref: str
    qty: int


@dataclass(frozen=True)
class LineAllocated(Event):
    order_id: str
    sku: str
    qty: int
    batch_ref: str


@dataclass(frozen=True)
class LineDeallocated(Event):
    order_id: str
    sku: str
    qty: int
    batch_ref: str
