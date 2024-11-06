from allocation.adapters.repository import DjangoRepository
from allocation.domain import model as domain_models
from dddjango.allocation import models as django_models
import pytest
from datetime import date


@pytest.mark.django_db
def test_can_create_obj_using_django_repository():
    domain_batch = domain_models.Batch('django-batch', 'skew', 10, eta=date.today())
    line1 = domain_models.OrderLine('order1', 'skew', 1)
    line2 = domain_models.OrderLine('order2', 'skew', 2)
    line3 = domain_models.OrderLine('order3', 'skew', 3)
    domain_batch.allocate(line1)
    domain_batch.allocate(line2)
    domain_batch.allocate(line3)
    
    repo = DjangoRepository()

    repo.add(domain_batch)
    django_batch = django_models.Batch.objects.get(reference='django-batch')

    assert django_batch.reference == domain_batch.reference
    assert django_batch.sku == domain_batch.sku
    assert django_batch.purchased_qty == domain_batch.allocated_qty + domain_batch.available_qty
    assert django_batch.eta == domain_batch.eta
    django_batch_allocations = django_models.Allocation.allocations_to_domain(django_batch)
    assert django_batch_allocations == domain_batch._allocations


@pytest.mark.django_db
def test_can_get_obj_using_django_repository():
    domain_batch = domain_models.Batch(
        reference='django-batch',
        sku='skew',
        purchased_qty=10,
        eta=date.today()
    )
    django_models.Batch.objects.create(**domain_batch.properties_dict)
    
    repo = DjangoRepository()
    retrieved_batch = repo.get(domain_batch.reference)

    assert retrieved_batch.reference == domain_batch.reference
    assert retrieved_batch.sku == domain_batch.sku
    assert retrieved_batch.allocated_qty == domain_batch.allocated_qty
    assert retrieved_batch.available_qty == domain_batch.available_qty
    assert retrieved_batch.eta == domain_batch.eta
    assert retrieved_batch._allocations == domain_batch._allocations
