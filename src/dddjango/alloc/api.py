from ninja import NinjaAPI
from allocation.domain import events
from allocation.domain.exceptions import (
    InexistentProduct, LineIsNotAllocatedError, OutOfStock
)
from allocation.orchestration import message_bus, services
from allocation.orchestration.uow import DjangoProductUoW
from dddjango.alloc.schemas import (
    BatchIn, BatchOut, BatchRef, Message, OrderLineIn
)


api = NinjaAPI()


@api.get('batches/{batch_ref}', response=BatchOut)
def get_batch_by_ref(request, batch_ref: str):
    with DjangoProductUoW() as uow:
        products = uow.products.list()
        batches = {b for p in products for b in p.batches}
        batch = next(batch for batch in batches if batch.ref == batch_ref)

    return 200, batch


@api.post('allocate', response = {201: BatchRef, 400: Message})
def allocate(request, payload: OrderLineIn):
    uow = DjangoProductUoW()
    line = payload.dict()
    try:
        results = message_bus.handle(
            events.AllocationRequired(line['order_id'], line['sku'], line['qty']),
            uow
        )
        if 'OutOfStock' in results:
            return 400, {'message': 'OutOfStock'}
        
        batch_ref = results[-1]

    except InexistentProduct:
        return 400, {'message': 'InexistentProduct'}
        
    return 201, {'batch_ref': batch_ref}


@api.post('deallocate', response = {200: BatchRef, 400: Message})
def deallocate(request, payload: OrderLineIn):
    uow = DjangoProductUoW()
    line = payload.dict()
    try:
        results = message_bus.handle(
            events.DeallocationRequired(line['order_id'], line['sku'], line['qty']),
            uow
        )
        batch_ref = results[-1]
    except InexistentProduct:
        return 400, {'message': 'InexistentProduct'}
    except LineIsNotAllocatedError:
        return 400, {'message': 'LineIsNotAllocatedError'}
        
    return 200, {'batch_ref': batch_ref}


@api.post('batches', response={201: BatchOut})
def add_batch(request, payload: BatchIn):
    uow = DjangoProductUoW()
    batch = payload.dict()
    message_bus.handle(events.BatchCreated(**batch), uow)
    added_batch = next(
        b for b in uow.products.get(batch['sku']).batches
        if b.ref == batch['ref']
    )

    return 201, added_batch
