from dataclasses import asdict, astuple
import os
import pickle
from allocation.domain import events, commands, model as domain_
from allocation.domain.exceptions import InexistentProduct, OutOfStock
from allocation.orchestration.uow import AbstractUnitOfWork
from allocation.adapters.redis_publisher import RedisEventPublisher
import redis


redis_client = redis.Redis(os.getenv('REDIS_HOST'), os.getenv('REDIS_PORT'))


def allocate(line: commands.Allocate, uow: AbstractUnitOfWork):
    with uow:
        product = uow.products.get(line.sku)

        try:
            batch_ref = product.allocate(line.order_id, line.sku, line.qty)
        except OutOfStock:
            uow.rollback()
            return 'OutOfStock'

        uow.commit()
    return batch_ref


def reallocate(line: commands.Reallocate, uow: AbstractUnitOfWork):
    return allocate(line, uow)


def deallocate(line: commands.Deallocate, uow: AbstractUnitOfWork):
    with uow:
        product = uow.products.get(line.sku)
        batch_ref = product.deallocate(line.order_id, line.sku, line.qty)
        uow.commit()
    return batch_ref


def add_batch(batch: commands.CreateBatch, uow: AbstractUnitOfWork) -> None:
    
    with uow:
        try:
            uow.products.get(sku=batch.sku).add_batch(*astuple(batch))
        
        except InexistentProduct:
            uow.products.add(domain_.Product(batch.sku))
            uow.products.get(sku=batch.sku).add_batch(*astuple(batch))
        uow.commit()
    return batch


def publish_event(event: events.Event, *args, **kwargs):
    redis_publisher = RedisEventPublisher(redis_client)
    redis_publisher.publish_event(event)
    

def change_batch_quantity(ref_and_qty: commands.ChangeBatchQuantity, uow: AbstractUnitOfWork):
    with uow:
        product = uow.products.get_by_batch_ref(ref_and_qty.ref)
        product.change_batch_quantity(ref_and_qty.ref, ref_and_qty.qty)
        uow.commit()

    return ref_and_qty.ref, ref_and_qty.qty


def add_batch_to_query_repository(batch_created: events.BatchCreated, *args, **kwargs):
    batch = pickle.dumps(domain_.Batch(**asdict(batch_created)))
    redis_client.hset('batches', batch_created.ref, batch)


def add_allocation_to_query_repository(line: events.LineAllocated, *args, **kwargs):
    redis_client.hset('allocation', f'{line.order_id}--{line.sku}', line.batch_ref)


def add_order_allocation_to_query_repository(line: events.LineAllocated, *args, **kwargs):
    new_allocation = {line.sku: line.batch_ref}
    allocations = redis_client.hget('order_allocations', line.order_id)

    if allocations is None:
        allocations = [new_allocation]
    else:
        allocations = pickle.loads(allocations)
        allocations.append(new_allocation)
    
    redis_client.hset('order_allocations', line.order_id, pickle.dumps(allocations))


def remove_allocation_from_query_repository(line: events.LineDeallocated, *args, **kwargs):
    redis_client.hdel('allocation', f'{line.order_id}--{line.sku}')


def remove_allocations_for_order_from_query_repository(line: events.LineDeallocated, *args, **kwargs):
    allocations = pickle.loads(redis_client.hget('order_allocations', line.order_id))
    allocations = [a for a in allocations if line.sku not in a]
    redis_client.hset('order_allocations', line.order_id, pickle.dumps(allocations))
