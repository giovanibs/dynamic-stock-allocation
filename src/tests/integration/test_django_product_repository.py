from allocation.adapters.repository import DjangoProductRepository
from allocation.domain import model as domain_models
from allocation.domain.exceptions import BatchDoesNotExist, InexistentProduct
from dddjango.alloc import models as django_models
import pytest


@pytest.fixture
def lines():
    return [
        domain_models.OrderLine('order1', 'skew', 1),
        domain_models.OrderLine('order2', 'skew', 2),
        domain_models.OrderLine('order3', 'skew', 3),
    ]


@pytest.fixture
def domain_batch(lines, today):
    batch = domain_models.Batch('batch', 'skew', 10, eta=today)
    line1 = lines[0]
    line2 = lines[1]
    line3 = lines[2]
    batch.allocate(line1)
    batch.allocate(line2)
    batch.allocate(line3)
    
    return batch


@pytest.fixture
def domain_product(domain_batch):
    return domain_models.Product(domain_batch.sku, [domain_batch])


@pytest.fixture
def repo():
    return DjangoProductRepository()


@pytest.mark.django_db
def test_can_create_a_product(lines, domain_product, repo):
    repo.add(domain_product)
    django_product = django_models.Product.objects.get(sku=domain_product.sku).to_domain()
    
    assert django_product.sku == domain_product.sku
    assert django_product.batches[0].reference == domain_product.batches[0].reference
    
    for line in lines:
        assert line in django_product.batches[0].allocations


@pytest.mark.django_db
def test_can_retrieve_a_product(repo):
    django_models.Product.objects.create(sku='skew')
    django_models.Product.objects.create(sku='sku')
    product = repo.get('sku').to_domain()
    assert product.sku == 'sku'


@pytest.mark.django_db
def test_cannot_retrieve_an_inexistent_product(repo):
    with pytest.raises(InexistentProduct):
        repo.get('inexistent_sku')


@pytest.mark.django_db
def test_can_update_product_after_adding_batch(repo):
    product = domain_models.Product('sku', [domain_models.Batch('batch', 'sku', 10)])
    repo.add(product)
    product.add_batch('other_batch', 'sku', 10)
    repo.update(product)
    updated_domain_product_from_db = repo.get('sku').to_domain()
    assert 'batch' in {b.reference for b in updated_domain_product_from_db.batches}
    assert 'other_batch' in {b.reference for b in updated_domain_product_from_db.batches}
