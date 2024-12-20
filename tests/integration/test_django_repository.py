from allocation.adapters.django_repository import DjangoRepository
from allocation.domain import model as domain_
from allocation.domain.exceptions import InexistentProduct
from dddjango.alloc import models as orm
import pytest


@pytest.fixture
def lines():
    return [
        domain_.OrderLine('order1', 'skew', 1),
        domain_.OrderLine('order2', 'skew', 2),
        domain_.OrderLine('order3', 'skew', 3),
    ]


@pytest.fixture
def domain_batch(lines, today):
    batch = domain_.Batch('batch', 'skew', 10, eta=today)
    line1 = lines[0]
    line2 = lines[1]
    line3 = lines[2]
    batch.allocate(line1)
    batch.allocate(line2)
    batch.allocate(line3)
    
    return batch


@pytest.fixture
def domain_product(domain_batch):
    return domain_.Product(domain_batch.sku, [domain_batch])


@pytest.fixture
def repo():
    return DjangoRepository()


@pytest.mark.django_db
def test_can_create_a_product(lines, domain_product, repo):
    repo.add(domain_product)
    orm_product = orm.Product.objects.get(sku=domain_product.sku).to_domain()
    
    assert orm_product.sku == domain_product.sku
    assert orm_product.batches[0].ref == domain_product.batches[0].ref
    
    for line in lines:
        assert line in orm_product.batches[0].allocations


@pytest.mark.django_db
def test_can_retrieve_a_product(repo):
    orm.Product.objects.create(sku='skew')
    orm.Product.objects.create(sku='sku')
    product = repo.get('sku')
    assert product.sku == 'sku'


@pytest.mark.django_db
def test_cannot_retrieve_an_inexistent_product(repo):
    with pytest.raises(InexistentProduct):
        repo.get('inexistent_sku')


@pytest.mark.django_db
def test_can_update_product_after_adding_batch(repo):
    product = domain_.Product('sku', [domain_.Batch('batch', 'sku', 10)])
    repo.add(product)
    product.add_batch('other_batch', 'sku', 10)
    repo.update(product)
    updated_domain_product_from_db = repo.get('sku')
    assert 'batch' in {b.ref for b in updated_domain_product_from_db.batches}
    assert 'other_batch' in {b.ref for b in updated_domain_product_from_db.batches}


@pytest.mark.django_db
def test_can_update_product_after_allocating_a_line(repo, domain_batch, domain_product):
    repo.add(domain_product)
    domain_product.allocate('new_line', domain_product.sku, 1)
    repo.update(domain_product)
    updated_domain_batch_from_db = repo.get(domain_product.sku).batches[0]
    
    assert set(updated_domain_batch_from_db.allocations) == set(domain_batch.allocations)


@pytest.mark.django_db
def test_can_update_product_after_deallocating_a_line(repo, domain_batch, domain_product, lines):
    repo.add(domain_product)
    domain_product.deallocate(lines[1].order_id, lines[1].sku, lines[1].qty)
    repo.update(domain_product)
    updated_domain_batch_from_db = repo.get(domain_product.sku).batches[0]
    
    assert set(updated_domain_batch_from_db.allocations) == set(domain_batch.allocations)


@pytest.mark.django_db
def test_can_return_list_of_products(repo):
    repo.add(domain_.Product('sku1'))
    repo.add(domain_.Product('sku2'))
    repo.add(domain_.Product('sku3'))
    products = repo.list()

    assert {'sku1', 'sku2', 'sku3'} == {p.sku for p in products}
