from allocation.adapters.repository import DjangoRepository
from allocation.domain import model as domain_models
from dddjango.allocation import models as django_models
import pytest
from datetime import date


@pytest.fixture
def domain_batch():
    batch = domain_models.Batch('batch', 'skew', 10, eta=date.today())
    line1 = domain_models.OrderLine('order1', 'skew', 1)
    line2 = domain_models.OrderLine('order2', 'skew', 2)
    line3 = domain_models.OrderLine('order3', 'skew', 3)
    batch.allocate(line1)
    batch.allocate(line2)
    batch.allocate(line3)
    
    return batch


@pytest.fixture
def repo():
    return DjangoRepository()


@pytest.mark.django_db
def test_can_create_object(domain_batch, repo):
    repo.add(domain_batch)
    django_batch = django_models.Batch.objects.get(reference=domain_batch.reference).to_domain()

    assert_batches_match(domain_batch, django_batch)


@pytest.mark.django_db
def test_can_get_object(repo):
    domain_batch = domain_models.Batch('batch', 'skew', 10, eta=date.today())
    django_models.Batch.objects.create(**domain_batch.properties_dict)
    retrieved_batch = repo.get(domain_batch.reference)

    assert_batches_match(domain_batch, retrieved_batch)


@pytest.mark.django_db
def test_can_update_object_with_new_line(domain_batch, repo):
   
    repo.add(domain_batch)
    brand_new_line = domain_models.OrderLine('order4', 'skew', 4)
    domain_batch.allocate(brand_new_line)
    repo.update(domain_batch)
    django_batch = repo.get(domain_batch.reference)

    assert_batches_match(domain_batch, django_batch)


@pytest.mark.django_db
def test_can_update_object_removing_line(domain_batch, repo):
   
    repo.add(domain_batch)
    domain_batch.deallocate(domain_batch.allocations[0])
    repo.update(domain_batch)
    django_batch = repo.get(domain_batch.reference)

    assert_batches_match(domain_batch, django_batch)


def assert_batches_match(batch: domain_models.Batch, other_batch: domain_models.Batch):
    assert batch.reference == other_batch.reference
    assert batch.sku == other_batch.sku
    assert batch.allocated_qty == other_batch.allocated_qty
    assert batch.available_qty == other_batch.available_qty
    assert batch.eta == other_batch.eta
    assert batch._allocations == other_batch._allocations
