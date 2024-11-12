from datetime import date
from typing import Optional
from allocation.domain import model as domain_
from allocation.domain.exceptions import InexistentProduct, ProductAlreadyExists
from allocation.orchestration.uow import AbstractUnitOfWork


def allocate(order_id: str, sku: str, qty: int, uow: AbstractUnitOfWork):
    with uow:
        product = uow.products.get(sku)
        batch_ref = product.allocate(order_id, sku, qty)
        uow.products.update(product)
        uow.commit()
    return batch_ref


def deallocate(order_id: str, sku: str, qty: int, uow: AbstractUnitOfWork):
    with uow:
        product = uow.products.get(sku)
        batch_ref = product.deallocate(order_id, sku, qty)
        uow.products.update(product)
        uow.commit()
    return batch_ref


def add_batch(ref: str,
              sku: str,
              qty: int,
              eta: Optional[date],
              uow: AbstractUnitOfWork
) -> None:
    batch = (ref, sku, qty, eta)
    with uow:
        try:
            uow.products.get(sku=sku).add_batch(*batch)
        except InexistentProduct:
            uow.products.add(domain_.Product(sku, [domain_.Batch(*batch)]))
        
        uow.commit()


def add_product(sku: str, uow: AbstractUnitOfWork) -> None:
    with uow:
        try:
            uow.products.get(sku=sku)
            raise ProductAlreadyExists()
        except InexistentProduct:
            uow.products.add(domain_.Product(sku))
        
        uow.commit()
