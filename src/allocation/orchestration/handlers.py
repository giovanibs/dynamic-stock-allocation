from dataclasses import astuple
import os
from allocation.domain import events, commands, model as domain_
from allocation.domain.exceptions import InexistentProduct, OutOfStock
from allocation.orchestration.uow import AbstractUnitOfWork
from allocation.adapters.redis_publisher import RedisEventPublisher
from allocation.adapters.redis_query_repository import RedisQueryRepository
import redis


redis_client = redis.Redis(os.getenv('REDIS_HOST'), os.getenv('REDIS_PORT'))
redis_repo = RedisQueryRepository(os.getenv('REDIS_HOST'), os.getenv('REDIS_PORT'))


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


def add_batch_to_query_repository(batch: events.BatchCreated, *args, **kwargs):
    redis_repo.add_batch(batch.ref, batch.sku, batch.qty, batch.eta)


def add_allocation_to_query_repository(line: events.LineAllocated, *args, **kwargs):
    redis_repo.add_allocation_for_line(line.order_id, line.sku, line.batch_ref)


def add_order_allocation_to_query_repository(line: events.LineAllocated, *args, **kwargs):
    redis_repo.add_allocation_for_order(line.order_id, line.sku, line.batch_ref)


def remove_allocation_from_query_repository(line: events.LineDeallocated, *args, **kwargs):
    redis_repo.remove_allocation_for_line(line.order_id, line.sku)


def remove_allocations_for_order_from_query_repository(line: events.LineDeallocated, *args, **kwargs):
    redis_repo.remove_allocation_for_order(line.order_id, line.sku)


def update_batch_quantity_in_query_repository(batch: events.BatchQuantityChanged, *args, **kwargs):
    redis_repo.update_batch_quantity(batch.ref, batch.qty)
    
