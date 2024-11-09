from allocation.orchestration.uow import DjangoUoW
from dddjango.alloc import models as dj_models
from allocation.domain import model as domain_models
import pytest


@pytest.mark.django_db(transaction=True)
def test_uow_can_retrieve_a_batch_and_allocate_to_it():
    insert_batch('batch', 'skew', 10)

    uow = DjangoUoW()

    with uow:
        batch = uow.batches.get(reference='batch')
        line = domain_models.OrderLine('o1', 'skew', 1)
        batch.allocate(line)
        uow.commit()

    batch_ref = get_allocated_batch_ref('o1', 'skew')
    assert batch_ref == 'batch'


def insert_batch(reference, sku, purchased_qty, eta=None):
    dj_models.Batch.objects.create(
        reference=reference,
        sku=sku,
        purchased_qty=purchased_qty,
        eta=eta
    )

def get_allocated_batch_ref(order_id, sku):
    allocation = dj_models.Allocation.objects.get(order_id=order_id, sku=sku)
    return allocation.batch.reference
