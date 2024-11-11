from allocation.orchestration.uow import DjangoProductUoW
from dddjango.alloc import models as django_models
from allocation.domain import model as domain_models
import pytest


@pytest.mark.django_db(transaction=True)
def test_uow_can_retrieve_a_product_and_add_a_batch():
    insert_product_into_db('skew')
    uow = DjangoProductUoW()

    with uow:
        product = uow.products.get('skew')
        product.add_batch('batch', 'skew', 10)
        uow.commit()

    assert retrieve_batch_from_db('batch').reference == 'batch'


@pytest.mark.django_db(transaction=True)
def test_uow_can_allocate_a_line():
    insert_product_into_db('skew')
    uow = DjangoProductUoW()

    with uow:
        product = uow.products.get('skew')
        product.add_batch('batch', 'skew', 10)
        product.allocate('o1', 'skew', 1)
        uow.commit()

    assert retrieve_batch_from_db('batch').allocations[0].order_id == 'o1'


@pytest.mark.django_db(transaction=True)
def test_uow_can_deallocate_a_line():
    sku = 'skew'
    db_product = insert_product_into_db(sku)
    db_batch = insert_batch_into_db('batch', db_product, 10)
    line = insert_allocation_into_db(db_batch, 'o1', sku , 1)
    
    uow = DjangoProductUoW()

    with uow:
        product = uow.products.get(sku)
        product.deallocate(line.order_id, sku, line.qty)
        uow.commit()

    assert len(retrieve_batch_from_db('batch').allocations) == 0


@pytest.mark.django_db(transaction=True)
def test_uow_does_not_commit_implicitly():
    uow = DjangoProductUoW()
    product = domain_models.Product('skew')
    with uow:
        uow.products.add(product)

    with pytest.raises(django_models.Product.DoesNotExist):
        django_models.Product.objects.get(sku=product.sku)


def insert_product_into_db(sku) -> django_models.Product:
    return django_models.Product.objects.create(sku=sku)


def retrieve_batch_from_db(reference) -> domain_models.Batch | None:
    try:
        return django_models.Batch.objects.get(reference=reference).to_domain()
    except django_models.Batch.DoesNotExist:
        return None
    

def insert_batch_into_db(reference, product, purchased_qty, eta=None) -> django_models.Batch:
    return django_models.Batch.objects.create(
        reference=reference,
        product=product,
        purchased_qty=purchased_qty,
        eta=eta
    )


def insert_allocation_into_db(batch, order_id, sku, qty) -> django_models.Allocation:
    return django_models.Allocation.objects.create(
        batch=batch,
        order_id=order_id,
        sku=sku,
        qty=qty,
    )    
