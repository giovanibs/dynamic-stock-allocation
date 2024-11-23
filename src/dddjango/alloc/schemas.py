from datetime import date
from typing import Dict, List, Optional, Union
from ninja import Schema


class BatchIn(Schema):
    ref: str
    sku: str
    qty: int
    eta: Optional[date] = None


class BatchOut(Schema):
    ref: str
    sku: str
    qty: int
    eta: Union[date, None]


class OrderLineIn(Schema):
    order_id: str
    sku: str
    qty: int


class BatchRef(Schema):
    batch_ref: str


class ErrorMessage(Schema):
    message: str


class AllocationsForOrder(Schema):
    allocations: List[Dict[str, str]]
