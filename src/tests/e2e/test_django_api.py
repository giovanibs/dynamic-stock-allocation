from datetime import date
from typing import Optional
from django.test import Client
import pytest


@pytest.fixture
def base_url():
    return '/api/'


@pytest.fixture
def client():
    return Client()


def post_to_create_batch(ref: str, sku: str, qty: int, eta: Optional[date]=None):
    response = Client().post(
        path = '/api/batches',
        data = {'reference': ref,'sku': sku,'purchased_qty': qty,'eta': eta},
        content_type = "application/json"
    )
    assert response.status_code == 201


def post_to_allocate_line(order_id: str, sku: str, qty: int):
    response = Client().post(
        path = '/api/allocate',
        data = {'order_id': order_id, 'sku': sku, 'qty': qty},
        content_type = "application/json"
    )
    assert response.status_code == 201


@pytest.mark.django_db
def test_can_retrieve_batch_info(base_url, client):
    batch = {'reference': 'ref', 'sku': 'skew', 'purchased_qty': 10, 'eta': None}
    post_to_create_batch(*batch.values())
    post_to_allocate_line('o1', 'skew', 1)
    post_to_allocate_line('o2', 'skew', 2)
    
    response = client.get(base_url + 'batches/' + batch['reference'])
    resp_batch = response.json()
    
    assert response.status_code == 200
    assert resp_batch['reference'] == batch['reference']
    assert resp_batch['sku'] == batch['sku']
    assert resp_batch['allocated_qty'] == 3
    assert resp_batch['available_qty'] == batch['purchased_qty'] - 3
    assert resp_batch['eta'] == batch['eta']


@pytest.mark.django_db
def test_api_returns_batch_ref_on_allocation(today, tomorrow, later, base_url, client):
    sku = 'skew'
    earliest_batch = ('today', sku, 10, today)
    in_between_batch = ('tomorrow', sku, 10, tomorrow)
    latest_batch = ('latest', sku, 10, later)
    post_to_create_batch(*earliest_batch)
    post_to_create_batch(*in_between_batch)
    post_to_create_batch(*latest_batch)
    line = {'order_id': 'o1', 'sku': sku, 'qty': 1}
    response = client.post(
        path = base_url + 'allocate',
        data = line,
        content_type = "application/json"
    )
    assert response.status_code == 201
    assert response.json()['batch_reference'] == earliest_batch[0]


@pytest.mark.django_db
def test_allocate_400_message_for_out_of_stock(base_url, client): 
    batch = ('batch', 'skew', 10)
    post_to_create_batch(*batch)
    line = {'order_id': 'o1', 'sku': 'skew', 'qty': 15}
    response = client.post(
        path = base_url + 'allocate',
        data = line,
        content_type = "application/json"
    )
    assert response.status_code == 400
    assert response.json()['message'] == 'OutOfStock'


@pytest.mark.django_db
def test_allocate_400_message_for_invalid_sku(base_url, client):
    line = {'order_id': 'o1', 'sku': 'skew', 'qty': 10}
    response = client.post(
        path = base_url + 'allocate',
        data = line,
        content_type = "application/json"
    )
    assert response.status_code == 400
    assert response.json()['message'] == 'InvalidSKU'


@pytest.mark.django_db
def test_api_returns_batch_ref_on_deallocation(base_url, client):
    batch = ('today', 'skew', 10)
    post_to_create_batch(*batch)
    line = {'order_id': 'o1', 'sku': 'skew', 'qty': 1}
    post_to_allocate_line(*line.values())
    response = client.post(
        path = base_url + 'deallocate',
        data = line,
        content_type = "application/json"
    )
    assert response.status_code == 200
    assert response.json()['batch_reference'] == batch[0]


@pytest.mark.django_db
def test_deallocate_400_message_for_invalid_sku(base_url, client):
    line = {'order_id': 'o1', 'sku': 'skew', 'qty': 1}
    response = client.post(
        path = base_url + 'deallocate',
        data = line,
        content_type = "application/json"
    )
    assert response.status_code == 400
    assert response.json()['message'] == 'InvalidSKU'


@pytest.mark.django_db
def test_deallocate_400_message_for_line_not_allocated(base_url, client): 
    batch = ('batch', 'skew', 10)
    post_to_create_batch(*batch)
    line = {'order_id': 'o1', 'sku': 'skew', 'qty': 1}
    response = client.post(
        path = base_url + 'deallocate',
        data = line,
        content_type = "application/json"
    )
    assert response.status_code == 400
    assert response.json()['message'] == 'LineIsNotAllocatedError'


@pytest.mark.django_db
def test_add_batch(base_url, client):
    batch = {'reference': 'batch', 'sku': 'skew', 'purchased_qty': 10, 'eta': None}
    response = client.post(
        base_url + 'batches', data=batch, content_type="application/json"
    )
    assert response.status_code == 201
    assert response.json()['reference'] == batch['reference']
    assert response.json()['sku'] == batch['sku']
    assert response.json()['available_qty'] == batch['purchased_qty']
    assert response.json()['eta'] == batch['eta']
