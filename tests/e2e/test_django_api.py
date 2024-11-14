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


class TestBatch:

    @pytest.mark.django_db(transaction=True)
    def test_add_batch(self, base_url, client):
        batch = {'ref': 'batch', 'sku': 'skew', 'qty': 10, 'eta': None}
        response = client.post(
            base_url + 'batches', data=batch, content_type="application/json"
        )
        assert response.status_code == 201
        assert response.json()['ref'] == batch['ref']
        assert response.json()['sku'] == batch['sku']
        assert response.json()['available_qty'] == batch['qty']
        assert response.json()['eta'] == batch['eta']


    @pytest.mark.django_db(transaction=True)
    def test_can_retrieve_batch_info(self, base_url, client):
        batch = {'ref': 'ref', 'sku': 'skew', 'qty': 10, 'eta': None}
        post_to_create_batch(*batch.values())
        
        response = client.get(base_url + 'batches/' + batch['ref'])
        resp_batch = response.json()
        
        assert response.status_code == 200
        assert resp_batch['ref'] == batch['ref']
        assert resp_batch['sku'] == batch['sku']
        assert resp_batch['allocated_qty'] == 0
        assert resp_batch['available_qty'] == batch['qty']
        assert resp_batch['eta'] == batch['eta']


class TestAllocate:
        
    @pytest.mark.django_db(transaction=True)
    def test_api_returns_batch_ref_on_allocation(self, today, tomorrow, later, base_url, client):
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
        assert response.json()['batch_ref'] == earliest_batch[0]


    @pytest.mark.django_db(transaction=True)
    def test_allocate_400_message_for_out_of_stock(self, base_url, client): 
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


    @pytest.mark.django_db(transaction=True)
    def test_allocate_400_message_for_inexistent_product(self, base_url, client):
        line = {'order_id': 'o1', 'sku': 'skew', 'qty': 10}
        response = client.post(
            path = base_url + 'allocate',
            data = line,
            content_type = "application/json"
        )
        assert response.status_code == 400
        assert response.json()['message'] == 'InexistentProduct'


class TestDeallocate:

    @pytest.mark.django_db(transaction=True)
    def test_api_returns_batch_ref_on_deallocation(self, base_url, client):
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
        assert response.json()['batch_ref'] == batch[0]


    @pytest.mark.django_db(transaction=True)
    def test_deallocate_400_message_for_inexistent_product(self, base_url, client):
        line = {'order_id': 'o1', 'sku': 'skew', 'qty': 1}
        response = client.post(
            path = base_url + 'deallocate',
            data = line,
            content_type = "application/json"
        )
        assert response.status_code == 400
        assert response.json()['message'] == 'InexistentProduct'


    @pytest.mark.django_db(transaction=True)
    def test_deallocate_400_message_for_line_not_allocated(self, base_url, client): 
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


def post_to_create_batch(ref: str, sku: str, qty: int, eta: Optional[date]=None):
    response = Client().post(
        path = '/api/batches',
        data = {'ref': ref,'sku': sku,'qty': qty,'eta': eta},
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