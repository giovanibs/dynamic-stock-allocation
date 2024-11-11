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
from allocation.domain.exceptions import InexistentProduct, ProductAlreadyExists
from allocation.orchestration.uow import AbstractProductUnitOfWork


def allocate(order_id: str, sku: str, qty: int, uow: AbstractProductUnitOfWork):
    with uow:
        product = uow.products.get(sku)
        batch_reference = product.allocate(order_id, sku, qty)
        uow.products.update(product)
        uow.commit()
    return batch_reference


def deallocate(order_id: str, sku: str, qty: int, uow: AbstractProductUnitOfWork):
    with uow:
        product = uow.products.get(sku)
        batch_reference = product.deallocate(order_id, sku, qty)
        uow.products.update(product)
        uow.commit()
    return batch_reference


def add_batch(reference: str,
              sku: str,
              purchased_qty: int,
              eta: Optional[date],
              uow: AbstractProductUnitOfWork
) -> None:
    batch = (reference, sku, purchased_qty, eta)
    with uow:
        try:
            uow.products.get(sku=sku).add_batch(*batch)
        except InexistentProduct:
            uow.products.add(domain_models.Product(sku, [domain_models.Batch(*batch)]))
        
        uow.commit()


def add_product(sku: str, uow: AbstractProductUnitOfWork) -> None:
    with uow:
        try:
            uow.products.get(sku=sku)
            raise ProductAlreadyExists()
        except InexistentProduct:
            uow.products.add(domain_models.Product(sku))
        
        uow.commit()
