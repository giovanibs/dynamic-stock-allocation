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
    def test_add_batch(self, today):
        batch = {'ref': 'batch', 'sku': 'skew', 'qty': 10, 'eta': today.isoformat()}
        response = post_to_create_batch(**batch)
        assert response.status_code == 201
        resp_batch = response.json()
        for field in batch:
            assert resp_batch[field] == batch[field]


    @pytest.mark.django_db(transaction=True)
    def test_can_retrieve_batch_info(self):
        batch = {'ref': 'ref', 'sku': 'skew', 'qty': 10, 'eta': None}
        post_to_create_batch(**batch)
        response = retrieve_batch_from_server(batch['ref'])
        resp_batch = response.json()
        for field in batch:
            assert resp_batch[field] == batch[field]


class TestAllocate:
        
    @pytest.mark.django_db(transaction=True)
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


    @pytest.mark.django_db(transaction=True)
    def test_allocate_400_message_for_out_of_stock(self): 
        batch = ('batch', 'skew', 10)
        post_to_create_batch(*batch)
        line = {'order_id': 'o1', 'sku': 'skew', 'qty': 15}
        response = post_to_allocate_line(**line, assert_ok=False)
        assert response.status_code == 400
        assert response.json()['message'] == 'OutOfStock'


    @pytest.mark.django_db(transaction=True)
    def test_allocate_400_message_for_inexistent_product(self):
        line = {'order_id': 'o1', 'sku': 'skew', 'qty': 10}
        response = post_to_allocate_line(**line, assert_ok=False)
        assert response.status_code == 400
        assert response.json()['message'] == 'InexistentProduct'


class TestDeallocate:

    @pytest.mark.django_db(transaction=True)
    def test_api_returns_batch_ref_on_deallocation(self):
        batch = ('today', 'skew', 10)
        post_to_create_batch(*batch)
        line = {'order_id': 'o1', 'sku': 'skew', 'qty': 1}
        post_to_allocate_line(**line)
        response = post_to_deallocate_line(**line)
        assert response.status_code == 200
        assert response.json()['batch_ref'] == batch[0]
    

    @pytest.mark.django_db(transaction=True)
    def test_deallocate_400_message_for_inexistent_product(self):
        line = {'order_id': 'o1', 'sku': 'skew', 'qty': 1}
        response = post_to_deallocate_line(**line, assert_ok=False)
        assert response.status_code == 400
        assert response.json()['message'] == 'InexistentProduct'


    @pytest.mark.django_db(transaction=True)
    def test_deallocate_400_message_for_line_not_allocated(self): 
        batch = ('batch', 'skew', 10)
        post_to_create_batch(*batch)
        line = {'order_id': 'o1', 'sku': 'skew', 'qty': 1}
        response = post_to_deallocate_line(**line, assert_ok=False)
        assert response.status_code == 400
        assert response.json()['message'] == 'LineIsNotAllocatedError'


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
