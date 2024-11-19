import pytest
from allocation.adapters.redis_query_repository import RedisQueryRepository
from allocation.domain import commands


@pytest.fixture
def redis_repo(redis_host, redis_port):
    return RedisQueryRepository(redis_host, redis_port)


@pytest.mark.django_db(transaction=True)
def test_can_query_batch_by_ref(today, redis_repo, bus, django_uow):
    batch = {'ref': 'batch', 'sku': 'sku', 'qty': 10, 'eta': today}
    bus.handle(commands.CreateBatch(**batch), django_uow)
    
    retrieved_batch = redis_repo.get_batch(batch['ref'])
    
    assert retrieved_batch.ref == batch['ref']
    assert retrieved_batch.sku == batch['sku']
    assert retrieved_batch.qty == batch['qty']
    assert retrieved_batch.eta == batch['eta']


@pytest.mark.django_db(transaction=True)
def test_can_query_batch_ref_for_allocation(today, redis_repo, bus, django_uow):
    batch = {'ref': 'batch', 'sku': 'sku', 'qty': 10, 'eta': today}
    line = {'order_id': 'o1', 'sku': 'sku', 'qty': 10}
    bus.handle(commands.CreateBatch(**batch), django_uow)
    bus.handle(commands.Allocate(**line), django_uow)
    
    batch_ref = redis_repo.allocation_for_line(line['order_id'], line['sku'])
    
    assert batch_ref.decode() == batch['ref']


@pytest.mark.django_db(transaction=True)
def test_can_query_allocations_for_order(tomorrow, redis_repo, bus, django_uow):
    order_id = 'order1'
    batch1 =  ('batch1', 'sku1', 10, tomorrow)
    batch2 =  ('batch2', 'sku2', 10, tomorrow)
    batch3 =  ('batch3', 'sku3', 10, tomorrow)
    line1 =  (order_id, 'sku1', 10)
    line2 =  (order_id, 'sku2', 10)
    line3 =  (order_id, 'sku3', 10)
    bus.handle(commands.CreateBatch(*batch1), django_uow)
    bus.handle(commands.CreateBatch(*batch2), django_uow)
    bus.handle(commands.CreateBatch(*batch3), django_uow)
    bus.handle(commands.Allocate(*line1), django_uow)
    bus.handle(commands.Allocate(*line2), django_uow)
    bus.handle(commands.Allocate(*line3), django_uow)
    
    allocations = redis_repo.allocations_for_order(order_id)
    
    assert allocations == [
                            {'sku1': 'batch1'},
                            {'sku2': 'batch2'},
                            {'sku3': 'batch3'},
                          ]


@pytest.mark.django_db(transaction=True)
def test_deallocation_updates_batch_ref(tomorrow, redis_repo, bus, django_uow):
    batch =  ('batch', 'sku', 10, tomorrow)
    line1 =  {'order_id': 'o1', 'sku': 'sku', 'qty': 5}
    line2 =  {'order_id': 'o2', 'sku': 'sku', 'qty': 5}
    bus.handle(commands.CreateBatch(*batch), django_uow)
    bus.handle(commands.Allocate(**line1), django_uow)
    bus.handle(commands.Allocate(**line2), django_uow)
    bus.handle(commands.Deallocate(**line1), django_uow)
    
    line1_batch_ref = redis_repo.allocation_for_line(line1['order_id'], line1['sku'])
    
    assert line1_batch_ref == None

    line2_batch_ref = redis_repo.allocation_for_line(line2['order_id'], line2['sku'])
    
    assert line2_batch_ref.decode() == 'batch'


@pytest.mark.django_db(transaction=True)
def test_deallocation_updates_order_allocations(tomorrow, redis_repo, bus, django_uow):
    order_id = 'order1'
    batch1 =  ('batch1', 'sku1', 10, tomorrow)
    batch2 =  ('batch2', 'sku2', 10, tomorrow)
    batch3 =  ('batch3', 'sku3', 10, tomorrow)
    line1 =  (order_id, 'sku1', 10)
    line2 =  (order_id, 'sku2', 10)
    line3 =  (order_id, 'sku3', 10)
    bus.handle(commands.CreateBatch(*batch1), django_uow)
    bus.handle(commands.CreateBatch(*batch2), django_uow)
    bus.handle(commands.CreateBatch(*batch3), django_uow)
    bus.handle(commands.Allocate(*line1), django_uow)
    bus.handle(commands.Allocate(*line2), django_uow)
    bus.handle(commands.Allocate(*line3), django_uow)
    bus.handle(commands.Deallocate(*line2), django_uow)
    
    allocations = redis_repo.allocations_for_order(order_id)
    
    assert allocations == [
                            {'sku1': 'batch1'},
                            {'sku3': 'batch3'},
                          ]


@pytest.mark.django_db(transaction=True)
def test_changing_batch_quantity_updates_batch(today, redis_repo, bus, django_uow):
    batch = {'ref': 'batch', 'sku': 'sku', 'qty': 10, 'eta': today}
    bus.handle(commands.CreateBatch(**batch), django_uow)
    
    retrieved_batch = redis_repo.get_batch(batch['ref'])
    assert retrieved_batch.qty == batch['qty']
    
    bus.handle(commands.ChangeBatchQuantity(batch['ref'], 5), django_uow)
    retrieved_batch = redis_repo.get_batch(batch['ref'])
    assert retrieved_batch.qty == 5
