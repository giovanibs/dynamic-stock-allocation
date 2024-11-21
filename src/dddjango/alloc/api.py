from ninja import NinjaAPI
from allocation.domain import commands
from allocation.domain.exceptions import (
    InexistentProduct, LineIsNotAllocatedError, OutOfStock, ValidationError
)
from allocation.orchestration import bootstrapper
from dddjango.alloc.schemas import (
    BatchIn, BatchOut, BatchRef, ErrorMessage, OrderLineIn
)


api = NinjaAPI()


@api.get('batches/{batch_ref}', response=BatchOut)
def get_batch_by_ref(request, batch_ref: str):
    bus = bootstrapper.bootstrap()
    with bus._uow as uow:
        products = uow.products.list()
        batches = {b for p in products for b in p.batches}
        batch = next(batch for batch in batches if batch.ref == batch_ref)

    return 200, batch


@api.post('allocate', response = {201: BatchRef, 400: ErrorMessage})
def allocate(request, payload: OrderLineIn):
    line = payload.dict()
    bus = bootstrapper.bootstrap()
    try:
        results = bus.handle(
            commands.Allocate(line['order_id'], line['sku'], line['qty'])
        )
    except OutOfStock:
        return 400, {'message': 'OutOfStock'}
    except InexistentProduct:
        return 400, {'message': 'InexistentProduct'}
    except ValidationError as validation_error:
        return 400, {'message': validation_error.message}
        
    batch_ref = results[-1]
    return 201, {'batch_ref': batch_ref}


@api.post('deallocate', response = {200: BatchRef, 400: ErrorMessage})
def deallocate(request, payload: OrderLineIn):
    line = payload.dict()
    bus = bootstrapper.bootstrap()
    try:
        results = bus.handle(
            commands.Deallocate(line['order_id'], line['sku'], line['qty'])
        )
        batch_ref = results[-1]
    except InexistentProduct:
        return 400, {'message': 'InexistentProduct'}
    except LineIsNotAllocatedError:
        return 400, {'message': 'LineIsNotAllocatedError'}
    except ValidationError as validation_error:
        return 400, {'message': validation_error.message}
        
        
    return 200, {'batch_ref': batch_ref}


@api.post('batches', response={201: BatchOut, 400: ErrorMessage})
def add_batch(request, payload: BatchIn):
    batch = payload.dict()
    bus = bootstrapper.bootstrap()
    try:
        bus.handle(commands.CreateBatch(**batch))
    except ValidationError as validation_error:
        return 400, {'message': validation_error.message}
    
    added_batch = next(
        b for b in bus._uow.products.get(batch['sku']).batches
        if b.ref == batch['ref']
    )
    return 201, added_batch
