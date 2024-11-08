from typing import Union
from ninja import NinjaAPI
from ninja.schema import Schema
from allocation.adapters.repository import DjangoRepository
from allocation.domain import model as domain_models
from allocation.domain.exceptions import InvalidSKU, LineIsNotAllocatedError, OutOfStock
from datetime import date

from allocation.orchestration import services


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


class FakeSession:
    def __init__(self) -> None:
        self._commited = False

    
    @property
    def commited(self):
        return self._commited
    
    
    def commit(self):
        self._commited = True


def get_session():
    return FakeSession()


@api.get('batches/{batch_ref}', response=BatchOut)
def get_batch_by_ref(request, batch_ref: str):
    return 200, repo.get(batch_ref)


@api.post('allocate', response = {201: BatchRef, 400: Message})
def allocate(request, payload: OrderLineIn):
    order_line = domain_models.OrderLine(**payload.dict())
    session = get_session()
    try:
        batch_ref = services.allocate(order_line, repo, session)
    except OutOfStock:
        return 400, {'message': 'OutOfStock'}
    except InvalidSKU:
        return 400, {'message': 'InvalidSKU'}
        
    return 201, {'batch_reference': batch_ref}


@api.post('deallocate', response = {200: BatchRef, 400: Message})
def deallocate(request, payload: OrderLineIn):
    order_line = domain_models.OrderLine(**payload.dict())
    session = get_session()
    try:
        batch_ref = services.deallocate(order_line, repo, session)
    except InvalidSKU:
        return 400, {'message': 'InvalidSKU'}
    except LineIsNotAllocatedError:
        return 400, {'message': 'LineIsNotAllocatedError'}
        
    return 200, {'batch_reference': batch_ref}

