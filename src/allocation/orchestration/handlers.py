from dataclasses import asdict, astuple
import logging
from allocation.domain import events, commands, model as domain_
from allocation.domain.exceptions import InexistentProduct
from allocation.orchestration.uow import AbstractUnitOfWork
from allocation.adapters.redis_publisher import redis_client, RedisEventPublisher


logger = logging.getLogger(__name__)


def allocate(line: commands.Allocate, uow: AbstractUnitOfWork):
    with uow:
        product = uow.products.get(line.sku)
        batch_ref = product.allocate(line.order_id, line.sku, line.qty)
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
            uow.products.add(
                domain_.Product(batch.sku, [domain_.Batch(*astuple(batch))])
            )
        uow.commit()
    return batch


def publish_event(event: events.Event, *args, **kwargs):
    redis_publisher = RedisEventPublisher(redis_client)
    logger.debug('Publishing %s', event)
    redis_publisher.publish_event(event)
    

def change_batch_quantity(ref_and_qty: commands.ChangeBatchQuantity, uow: AbstractUnitOfWork):
    with uow:
        product = uow.products.get_by_batch_ref(ref_and_qty.ref)
        product.change_batch_quantity(ref_and_qty.ref, ref_and_qty.qty)
        uow.commit()

    return ref_and_qty.ref, ref_and_qty.qty
