from dataclasses import astuple
from allocation.domain import events, commands, model as domain_
from allocation.domain.exceptions import InexistentProduct, OutOfStock
from allocation.orchestration.uow import AbstractUnitOfWork


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


def publish_event(event: events.Event, uow: AbstractUnitOfWork):
    uow.publisher.publish_event(event)
    

def change_batch_quantity(ref_and_qty: commands.ChangeBatchQuantity, uow: AbstractUnitOfWork):
    with uow:
        product = uow.products.get_by_batch_ref(ref_and_qty.ref)
        product.change_batch_quantity(ref_and_qty.ref, ref_and_qty.qty)
        uow.commit()

    return ref_and_qty.ref, ref_and_qty.qty
