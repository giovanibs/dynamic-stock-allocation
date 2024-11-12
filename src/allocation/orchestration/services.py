from datetime import date
from typing import Optional
from allocation.domain import model as domain_models
from allocation.domain.exceptions import InexistentProduct, ProductAlreadyExists
from allocation.orchestration.uow import AbstractUnitOfWork


def allocate(order_id: str, sku: str, qty: int, uow: AbstractUnitOfWork):
    with uow:
        product = uow.products.get(sku)
        batch_reference = product.allocate(order_id, sku, qty)
        uow.products.update(product)
        uow.commit()
    return batch_reference


def deallocate(order_id: str, sku: str, qty: int, uow: AbstractUnitOfWork):
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
              uow: AbstractUnitOfWork
) -> None:
    batch = (reference, sku, purchased_qty, eta)
    with uow:
        try:
            uow.products.get(sku=sku).add_batch(*batch)
        except InexistentProduct:
            uow.products.add(domain_models.Product(sku, [domain_models.Batch(*batch)]))
        
        uow.commit()


def add_product(sku: str, uow: AbstractUnitOfWork) -> None:
    with uow:
        try:
            uow.products.get(sku=sku)
            raise ProductAlreadyExists()
        except InexistentProduct:
            uow.products.add(domain_models.Product(sku))
        
        uow.commit()
