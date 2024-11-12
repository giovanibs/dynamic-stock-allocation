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
