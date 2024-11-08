from django.test import Client
import pytest
from allocation.adapters.repository import DjangoRepository
from allocation.domain import model as domain_models


@pytest.fixture
def base_url():
    return '/api/'


@pytest.fixture
def repo():
    return DjangoRepository()


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_can_retrieve_batch_info(base_url, client, repo):
    batch = domain_models.Batch('ref', 'skew', 10)
    line1 = domain_models.OrderLine('o1', 'skew', 1)
    line2 = domain_models.OrderLine('o2', 'skew', 2)
    batch.allocate(line1)
    batch.allocate(line2)
    repo.add(batch)
    
    response = client.get(base_url + 'batches/' + batch.reference)
    resp_batch = response.json()
    
    assert response.status_code == 200
    assert resp_batch['reference'] == batch.reference
    assert resp_batch['sku'] == batch.sku
    assert resp_batch['allocated_qty'] == batch.allocated_qty
    assert resp_batch['available_qty'] == batch.available_qty
    assert resp_batch['eta'] == batch.eta


@pytest.mark.django_db
def test_api_returns_batch_ref_on_allocation(today, tomorrow, later, base_url, client, repo):
    sku = 'skew'
    earliest_batch = domain_models.Batch('today', sku, 10, eta=today)
    in_between_batch = domain_models.Batch('tomorrow', sku, 10, eta=tomorrow)
    latest_batch = domain_models.Batch('latest', sku, 10, eta=later)
    repo.add(earliest_batch)
    repo.add(in_between_batch)
    repo.add(latest_batch)
    line = {'order_id': 'o1', 'sku': sku, 'qty': 1}
    response = client.post(base_url + 'allocate', data = line, content_type = "application/json")
    assert response.status_code == 201
    assert response.json()['batch_reference'] == earliest_batch.reference


@pytest.mark.django_db
def test_400_message_for_out_of_stock(base_url, client, repo): 
    batch = domain_models.Batch('batch', 'skew', 10)
    repo.add(batch)
    line = {'order_id': 'o1', 'sku': 'skew', 'qty': 15}
    response = client.post(base_url + 'allocate', data = line, content_type = "application/json")
    assert response.status_code == 400
    assert response.json()['message'] == 'OutOfStock'


@pytest.mark.django_db
def test_400_message_for_invalid_sku(base_url, client, repo):
    batch = domain_models.Batch('batch', 'skew', 10)
    repo.add(batch)
    line = {'order_id': 'o1', 'sku': 'skewer', 'qty': 10}
    response = client.post(base_url + 'allocate', data = line, content_type = "application/json")
    assert response.status_code == 400
    assert response.json()['message'] == 'InvalidSKU'
