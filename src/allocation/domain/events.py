from dataclasses import dataclass


class Event:
    pass


@dataclass(frozen=True)
class OutOfStock(Event):
    sku: str
