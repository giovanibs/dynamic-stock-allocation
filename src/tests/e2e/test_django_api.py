from django.test import Client
import pytest
from allocation.adapters.repository import DjangoRepository
from allocation.domain import model as domain_models


@pytest.mark.django_db
def test_can_retrieve_batch_info():
    base_url = 'http://127.0.0.1:8000/api/'
    repo = DjangoRepository()
    client = Client()

    batch = domain_models.Batch('ref', 'skew', 10)
    line1 = domain_models.OrderLine('o1', 'skew', 1)
    line2 = domain_models.OrderLine('o2', 'skew', 2)
    batch.allocate(line1)
    batch.allocate(line2)
    repo.add(batch)
    
    response = client.get(base_url + batch.reference)
    resp_batch = response.json()
    
    assert response.status_code == 200
    assert resp_batch['reference'] == batch.reference
    assert resp_batch['sku'] == batch.sku
    assert resp_batch['allocated_qty'] == batch.allocated_qty
    assert resp_batch['available_qty'] == batch.available_qty
    assert resp_batch['eta'] == batch.eta
