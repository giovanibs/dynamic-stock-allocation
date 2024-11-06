from allocation.adapters.repository import DjangoRepository
from allocation.domain.model import Batch
from src.dddjango.allocation import models as django_models
import pytest


@pytest.mark.django_db
def test_can_create_obj_using_django_repository():
    batch = Batch(
        reference='django-batch',
        sku='skew',
        purchased_qty=10,
        eta=None
    )
    repo = DjangoRepository()

    repo.add(batch)

    django_batch = django_models.Batch.objects.first()

    assert django_batch.reference == batch.reference
    assert django_batch.sku == batch.sku
    assert django_batch.purchased_qty == batch.allocated_qty + batch.available_qty
    assert django_batch.eta == batch.eta


@pytest.mark.django_db
def test_can_get_obj_using_django_repository():
    batch = Batch(
        reference='django-batch',
        sku='skew',
        purchased_qty=10,
        eta=None
    )
    django_models.Batch.objects.create(**batch.properties_dict)
    
    repo = DjangoRepository()
    retrieved_batch = repo.get(batch.reference)

    assert retrieved_batch.reference == batch.reference
    assert retrieved_batch.sku == batch.sku
    assert retrieved_batch.allocated_qty == batch.allocated_qty
    assert retrieved_batch.available_qty == batch.available_qty
    assert retrieved_batch.eta == batch.eta
