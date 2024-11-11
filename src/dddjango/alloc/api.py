from ninja import NinjaAPI
from allocation.domain.exceptions import InvalidSKU, LineIsNotAllocatedError, OutOfStock, ProductAlreadyExists
from allocation.orchestration import services
from allocation.orchestration.uow import DjangoProductUoW, DjangoUoW
from dddjango.alloc.schemas import (
    BatchIn, BatchOut, BatchRef, Message, OrderLineIn, ProductIn, ProductOut
)


api = NinjaAPI()


@api.post('products', response={201: ProductOut, 400: Message})
def add_product(request, payload: ProductIn):
    uow = DjangoProductUoW()
    product = payload.dict()
    
    try:
        services.add_product(*product.values(), uow)
    except ProductAlreadyExists:
        return 400, {'message': 'ProductAlreadyExists'}
    
    added_product = uow.products.get(product['sku'])

    return 201, added_product


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
    uow = DjangoProductUoW()
    batch = payload.dict()
    services.add_batch(*batch.values(), uow)
    added_batch = next(
        b for b in uow.products.get(batch['sku']).batches
        if b.reference == batch['reference']
    )

    return 201, added_batch
