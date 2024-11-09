from ninja import NinjaAPI
from allocation.domain.exceptions import InvalidSKU, LineIsNotAllocatedError, OutOfStock
from allocation.orchestration import services
from allocation.orchestration.uow import DjangoUoW
from dddjango.alloc.schemas import BatchIn, BatchOut, BatchRef, Message, OrderLineIn


api = NinjaAPI()


@api.get('batches/{batch_ref}', response=BatchOut)
def get_batch_by_ref(request, batch_ref: str):
    uow = DjangoUoW()
    with uow:
        batch = uow.batches.get(batch_ref)

    return 200, batch


@api.post('allocate', response = {201: BatchRef, 400: Message})
def allocate(request, payload: OrderLineIn):
    uow = DjangoUoW()
    line = payload.dict()
    try:
        batch_ref = services.allocate(
            line['order_id'], line['sku'], line['qty'], uow
        )
    except OutOfStock:
        return 400, {'message': 'OutOfStock'}
    except InvalidSKU:
        return 400, {'message': 'InvalidSKU'}
        
    return 201, {'batch_reference': batch_ref}


@api.post('deallocate', response = {200: BatchRef, 400: Message})
def deallocate(request, payload: OrderLineIn):
    uow = DjangoUoW()
    line = payload.dict()
    try:
        batch_ref = services.deallocate(
            line['order_id'], line['sku'], line['qty'], uow
        )
    except InvalidSKU:
        return 400, {'message': 'InvalidSKU'}
    except LineIsNotAllocatedError:
        return 400, {'message': 'LineIsNotAllocatedError'}
        
    return 200, {'batch_reference': batch_ref}


@api.post('batches', response={201: BatchOut})
def add_batch(request, payload: BatchIn):
    uow = DjangoUoW()
    batch = payload.dict()
    services.add_batch(*batch.values(), uow)
    added_batch = uow.batches.get(batch['reference'])

    return 201, added_batch
