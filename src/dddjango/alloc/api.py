import ninja
from allocation.domain import commands, queries
from allocation.domain import exceptions
from allocation.orchestration import bootstrapper
from dddjango.alloc.schemas import (
    AllocationsForOrder, BatchIn, BatchOut, BatchRef, ErrorMessage, OrderLineIn
)


api = ninja.NinjaAPI()


@api.get('batches/{batch_ref}', response=BatchOut)
def get_batch_by_ref(request, batch_ref: str):
    bus = bootstrapper.bootstrap()
    batch = bus.handle(queries.BatchByRef(batch_ref))
    return 200, batch


@api.post('allocate', response = {201: BatchRef, 400: ErrorMessage})
def allocate(request, payload: OrderLineIn):
    line = payload.dict()
    bus = bootstrapper.bootstrap()
    results = bus.handle(
        commands.Allocate(line['order_id'], line['sku'], line['qty'])
    )
    batch_ref = results[-1]
    return 201, {'batch_ref': batch_ref}


@api.post('deallocate', response = {200: BatchRef, 400: ErrorMessage})
def deallocate(request, payload: OrderLineIn):
    line = payload.dict()
    bus = bootstrapper.bootstrap()
    results = bus.handle(
        commands.Deallocate(line['order_id'], line['sku'], line['qty'])
    )
    batch_ref = results[-1]
        
    return 200, {'batch_ref': batch_ref}


@api.post('batches', response={201: BatchOut})
def add_batch(request, payload: BatchIn):
    batch = payload.model_dump()
    bus = bootstrapper.bootstrap()
    bus.handle(commands.CreateBatch(**batch))
    
    added_batch = next(
        b for b in bus._uow.products.get(batch['sku']).batches
        if b.ref == batch['ref']
    )
    return 201, added_batch


@api.get('allocations/{order_id}/{sku}', response={200: BatchRef, 400: ErrorMessage})
def query_allocation_for_line(request, order_id, sku):
    bus = bootstrapper.bootstrap()
    batch_ref = bus.handle(queries.AllocationForLine(order_id, sku))
    return 200, {'batch_ref': batch_ref}


@api.get('allocations/{order_id}', response = { 200: AllocationsForOrder,
                                                400: ErrorMessage})
def query_allocations_for_order(request, order_id):
    bus = bootstrapper.bootstrap()
    allocations = bus.handle(queries.AllocationsForOrder(order_id))
    return 200, {'allocations': allocations}


@api.exception_handler(exceptions.DomainException)
def domain_error(request, exc):
    return api.create_response(
        request,
        {"message": exc.msg},
        status=400,
    )


@api.exception_handler(exceptions.ValidationError)
def validation_error(request, exc):
    return api.create_response(
        request,
        {"message": exc.msg},
        status=400,
    )


@api.exception_handler(ninja.errors.ValidationError)
def ninja_validation_errors(request, exc):
    errors = [error['loc'][2] for error in exc.errors]
    
    if 'qty' in errors:
        error = exceptions.InvalidTypeForQuantity()
    elif 'eta' in errors:
        error = exceptions.InvalidETAFormat()
    
    return api.create_response(
        request,
        {"message": error.msg},
        status=400,
    )
