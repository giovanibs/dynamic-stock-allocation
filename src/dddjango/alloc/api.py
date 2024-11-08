from typing import Union
from ninja import NinjaAPI
from ninja.schema import Schema
from allocation.adapters.repository import DjangoRepository
from allocation.domain import model as domain_models
from allocation.domain.exceptions import InvalidSKU, OutOfStock
from datetime import date


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


api = NinjaAPI()
repo = DjangoRepository()


@api.get('batches/{batch_ref}', response=BatchOut)
def get_batch_by_ref(request, batch_ref: str):
    return 200, repo.get(batch_ref)


@api.post('allocate', response = {201: BatchRef, 400: Message})
def allocate(request, payload: OrderLineIn):
    order_line = domain_models.OrderLine(**payload.dict())
    batches = repo.list()
    
    try:
        batch_ref = domain_models.allocate(order_line, batches)
    except OutOfStock:
        return 400, {'message': 'OutOfStock'}
    except InvalidSKU:
        return 400, {'message': 'InvalidSKU'}
        
    repo.update(next(b for b in batches if b.reference == batch_ref))
    return 201, {'batch_reference': batch_ref}
