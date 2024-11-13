from dataclasses import astuple
import logging
import os
from allocation.domain import events, commands, model as domain_
from allocation.domain.exceptions import InexistentProduct
from allocation.orchestration.uow import AbstractUnitOfWork


def allocate(line: commands.Allocate, uow: AbstractUnitOfWork):
    with uow:
        product = uow.products.get(line.sku)
        batch_ref = product.allocate(line.order_id, line.sku, line.qty)
        uow.commit()
    return batch_ref


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


def notify(event: events.OutOfStock, uow: AbstractUnitOfWork):
    logger = logging.getLogger(__name__)

    if logger.hasHandlers():
        logger.handlers.clear()

    filename = os.path.join(os.getcwd(), 'notify.log')
    file_handler = logging.FileHandler(filename, mode='w')
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    logger.warning(f"'{event.sku}' is out of stock!")

    return 'OutOfStock' # for returning error msg


def change_batch_quantity(ref_and_qty: commands.ChangeBatchQuantity, uow: AbstractUnitOfWork):
    with uow:
        product = uow.products.get_by_batch_ref(ref_and_qty.ref)
        product.change_batch_quantity(ref_and_qty.ref, ref_and_qty.qty)
        uow.commit()

    return ref_and_qty.ref, ref_and_qty.qty