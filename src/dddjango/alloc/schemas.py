from datetime import date
from typing import Optional, Union
from ninja import Schema


class BatchIn(Schema):
    reference: str
    sku: str
    purchased_qty: int
    eta: Optional[date] = None


class BatchOut(Schema):
    reference: str
    sku: str
    allocated_qty: int
    available_qty: int
    eta: Union[date, None]


class OrderLineIn(Schema):
    order_id: str
    sku: str
    qty: int


class BatchRef(Schema):
    batch_reference: str


class Message(Schema):
    message: str
