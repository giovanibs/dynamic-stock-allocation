"""
Typical service-layer functions have similar steps:

(1) We fetch some objects from the repository.
(2) We make some checks or assertions about the request against the current state of the world.
(3) We call a domain service.
(4) If all is well, we save/update any state we’ve changed.
"""
from datetime import date
from typing import Optional
from allocation.domain import model as domain_models
from allocation.domain.exceptions import InvalidSKU
from allocation.orchestration.uow import AbstractUnitOfWork


def allocate(order_id: str, sku: str, qty: int, uow: AbstractUnitOfWork):
    with uow:
        batches = uow.batches.list()
    
        if sku not in {batch.sku for batch in batches}:
            raise InvalidSKU()
        
        batch_reference = domain_models.allocate(order_id, sku, qty, batches)
        uow.batches.update(next(b for b in batches if b.reference == batch_reference))
        uow.commit()
    return batch_reference


def deallocate(order_id: str, sku: str, qty: int, uow: AbstractUnitOfWork):
    with uow:
        batches = uow.batches.list()
        batch_reference = domain_models.deallocate(order_id, sku, qty, batches)
        uow.batches.update(next(b for b in batches if b.reference == batch_reference))
        uow.commit()
    return batch_reference


def add_batch(reference: str,
              sku: str,
              purchased_qty: int,
              eta: Optional[date],
              uow: AbstractUnitOfWork):
    
    with uow:
        uow.batches.add(domain_models.Batch(reference, sku, purchased_qty, eta))
        uow.commit()
