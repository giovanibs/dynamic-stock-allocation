from allocation.domain.exceptions import InvalidSKU
from allocation.orchestration.uow import DjangoUoW
from dddjango.alloc import models as orm
from allocation.domain import model as domain_
import pytest


@pytest.mark.django_db(transaction=True)
def test_uow_can_retrieve_a_product_and_add_a_batch():
    insert_product_into_db('skew')
    uow = DjangoUoW()

    with uow:
        product = uow.products.get('skew')
        product.add_batch('batch', 'skew', 10)
        uow.commit()

    assert retrieve_batch_from_db('batch').ref == 'batch'


@pytest.mark.django_db(transaction=True)
def test_uow_can_allocate_a_line():
    insert_product_into_db('skew')
    uow = DjangoUoW()

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
    
    uow = DjangoUoW()

    with uow:
        product = uow.products.get(sku)
        product.deallocate(line.order_id, sku, line.qty)
        uow.commit()

    assert len(retrieve_batch_from_db('batch').allocations) == 0


@pytest.mark.django_db(transaction=True)
def test_uow_does_not_commit_implicitly():
    uow = DjangoUoW()
    with uow:
        insert_product_into_db('skew')

    with pytest.raises(orm.Product.DoesNotExist):
        orm.Product.objects.get(sku='skew')


@pytest.mark.django_db(transaction=True)
def test_uow_rollbacks_on_error():
    sku = 'skew'
    insert_product_into_db(sku)
    invalid_line = ('o1', 'invalid_sku', 1)

    try:
        with DjangoUoW() as uow:
            product = uow.products.get(sku)
            insert_batch_into_db('batch', orm.Product.objects.get(sku=sku), 10)
            product.allocate(*invalid_line)
            uow.commit()
    except InvalidSKU:
        pass

    assert retrieve_batch_from_db('batch') is None


def insert_product_into_db(sku) -> orm.Product:
    return orm.Product.objects.create(sku=sku)


def retrieve_batch_from_db(ref) -> domain_.Batch | None:
    try:
        return orm.Batch.objects.get(ref=ref).to_domain()
    except orm.Batch.DoesNotExist:
        return None
    

def insert_batch_into_db(ref, product: orm.Product, qty, eta=None) -> orm.Batch:
    return orm.Batch.objects.create(
        ref=ref,
        product=product,
        qty=qty,
        eta=eta
    )


def insert_allocation_into_db(batch, order_id, sku, qty) -> orm.Allocation:
    return orm.Allocation.objects.create(
        batch=batch,
        order_id=order_id,
        sku=sku,
        qty=qty,
    )    
