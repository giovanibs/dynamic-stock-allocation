from django.test import Client
import pytest
from allocation.domain import exceptions


@pytest.fixture(scope="function")
def clear_redis(redis_client):
    redis_client.flushall()
    yield
    redis_client.flushall()


@pytest.mark.django_db(transaction=True)
class TestBatch:

    def test_add_batch(self, today):
        batch = {'ref': 'batch', 'sku': 'skew', 'qty': 10, 'eta': today.isoformat()}
        response = post_to_create_batch(**batch)
        assert response.status_code == 201
        resp_batch = response.json()
        for field in batch:
            assert resp_batch[field] == batch[field]


    @pytest.mark.usefixtures('clear_redis')
    def test_can_retrieve_batch_info(self):
        batch = {'ref': 'ref', 'sku': 'skew', 'qty': 10, 'eta': None}
        post_to_create_batch(**batch)
        response = retrieve_batch_from_server(batch['ref'])
        resp_batch = response.json()
        for field in batch:
            assert resp_batch[field] == batch[field]
    

    @pytest.mark.parametrize(
        ('values', 'error_msg'),
        [
            (('batch', 'sku', 'a'), exceptions.InvalidTypeForQuantity().message),
            (('batch', 'sku', -1), exceptions.InvalidQuantity().message),
            (('batch', 'sku', 1, 'aaaaa'), exceptions.InvalidETAFormat().message),
            (('batch', 'sku', 1, '1900-01-01'), exceptions.PastETANotAllowed().message),
        ]
    )
    def test_invalid_values_return_error_message(self, values, error_msg):
        response = post_to_create_batch(*values, assert_ok=False)
        assert response.status_code == 400
        assert response.json()['message'] == error_msg
    

    @pytest.mark.usefixtures('clear_redis')
    def test_batch_does_not_exist(self):
        response = retrieve_batch_from_server('inexistent', assert_ok=False)
        assert response.status_code == 400
        assert response.json()['message'] == exceptions.BatchDoesNotExist().message


@pytest.mark.django_db(transaction=True)
class TestAllocate:
        
    def test_api_returns_batch_ref_on_allocation(self, today, tomorrow, later):
        sku = 'skew'
        earliest_batch = ('today', sku, 10, today)
        in_between_batch = ('tomorrow', sku, 10, tomorrow)
        latest_batch = ('latest', sku, 10, later)
        post_to_create_batch(*earliest_batch)
        post_to_create_batch(*in_between_batch)
        post_to_create_batch(*latest_batch)
        line = {'order_id': 'o1', 'sku': sku, 'qty': 1}
        response = post_to_allocate_line(**line)
        assert response.status_code == 201
        assert response.json()['batch_ref'] == earliest_batch[0]


    @pytest.mark.parametrize(
        ('line', 'error_message'),
        [
            (('o1', 'inexistent', 1), exceptions.InexistentProduct().message),
            (('o1', 'skew', 1_000), exceptions.OutOfStock().message),
            (('o1', 'skew', 'a'), exceptions.InvalidTypeForQuantity().message),
            (('o1', 'skew', -1), exceptions.InvalidQuantity().message),
        ]
    )
    def test_allocate_400_errors(self, line, error_message): 
        batch = ('batch', 'skew', 10)
        post_to_create_batch(*batch)
        response = post_to_allocate_line(*line, assert_ok=False)
        assert response.status_code == 400
        assert response.json()['message'] == error_message


@pytest.mark.django_db(transaction=True)
class TestDeallocate:

    def test_api_returns_batch_ref_on_deallocation(self):
        batch = ('today', 'skew', 10)
        post_to_create_batch(*batch)
        line = {'order_id': 'o1', 'sku': 'skew', 'qty': 1}
        post_to_allocate_line(**line)
        response = post_to_deallocate_line(**line)
        assert response.status_code == 200
        assert response.json()['batch_ref'] == batch[0]
    

    @pytest.mark.parametrize(
        ('line', 'error_message'),
        [
            (('o1', 'inexistent', 1), exceptions.InexistentProduct().message),
            (('o1', 'skew', 1), exceptions.LineIsNotAllocatedError().message),
            (('o1', 'skew', 'a'), exceptions.InvalidTypeForQuantity().message),
            (('o1', 'skew', -1), exceptions.InvalidQuantity().message),
        ]
    )
    def test_deallocate_400_errors(self, line, error_message):
        batch = ('batch', 'skew', 10)
        post_to_create_batch(*batch)
        response = post_to_deallocate_line(*line, assert_ok=False)
        assert response.status_code == 400
        assert response.json()['message'] == error_message


def post_to_create_batch(ref, sku, qty, eta=None, assert_ok=True):
    response = Client().post(
        path = '/api/batches',
        data = {'ref': ref,'sku': sku,'qty': qty,'eta': eta},
        content_type = "application/json"
    )
    if assert_ok:
        assert response.status_code == 201
    
    return response


def post_to_allocate_line(order_id, sku, qty, assert_ok=True):
    response = Client().post(
        path = '/api/allocate',
        data = {'order_id': order_id, 'sku': sku, 'qty': qty},
        content_type = "application/json"
    )
    if assert_ok:
        assert response.status_code == 201
    
    return response


def post_to_deallocate_line(order_id, sku, qty, assert_ok=True):
    response = Client().post(
        path = '/api/deallocate',
        data = {'order_id': order_id, 'sku': sku, 'qty': qty},
        content_type = "application/json"
    )
    if assert_ok:
        assert response.status_code == 200
    
    return response


def retrieve_batch_from_server(ref, assert_ok=True):
    response = Client().get(path = f'/api/batches/{ref}')
    if assert_ok:
        assert response.status_code == 200
    
    return response
