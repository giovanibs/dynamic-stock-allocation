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


def insert_product_into_db(sku) -> None:
    django_models.Product.objects.create(sku=sku)


def retrieve_batch_from_db(reference) -> domain_models.Batch | None:
    try:
        return django_models.Batch.objects.get(reference=reference).to_domain()
    except django_models.Batch.DoesNotExist:
        return None
