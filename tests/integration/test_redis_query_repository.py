import pytest
from allocation.adapters.redis_query_repository import RedisQueryRepository
from allocation.domain import commands, queries
from allocation.orchestration import bootstrapper


@pytest.fixture
def redis_repo(redis_host, redis_port):
    return RedisQueryRepository(redis_host, redis_port)


@pytest.fixture
def bus(redis_repo):
    return bootstrapper.bootstrap(query_repository=redis_repo)


@pytest.fixture(scope="function", autouse=True)
def clear_redis(redis_client):
    redis_client.flushall()
    yield
    redis_client.flushall()


@pytest.mark.django_db(transaction=True)
def test_can_query_batch_by_ref(today, bus):
    batch = {'ref': 'batch', 'sku': 'sku', 'qty': 10, 'eta': today}
    bus.handle(commands.CreateBatch(**batch))
    retrieved_batch = bus.handle(queries.BatchByRef(batch['ref']))
    assert retrieved_batch.ref == batch['ref']
    assert retrieved_batch.sku == batch['sku']
    assert retrieved_batch.qty == batch['qty']
    assert retrieved_batch.eta == batch['eta']


@pytest.mark.django_db(transaction=True)
def test_can_query_batch_ref_for_allocation(today, bus):
    batch = {'ref': 'batch', 'sku': 'sku', 'qty': 10, 'eta': today}
    line = {'order_id': 'o1', 'sku': 'sku', 'qty': 10}
    bus.handle(commands.CreateBatch(**batch))
    bus.handle(commands.Allocate(**line))
    batch_ref = bus.handle(queries.AllocationForLine(line['order_id'], line['sku']))
    assert batch_ref.decode() == batch['ref']


@pytest.mark.django_db(transaction=True)
def test_can_query_allocations_for_order(tomorrow, bus):
    order_id = 'order1'
    batch1 =  ('batch1', 'sku1', 10, tomorrow)
    batch2 =  ('batch2', 'sku2', 10, tomorrow)
    batch3 =  ('batch3', 'sku3', 10, tomorrow)
    line1 =  (order_id, 'sku1', 10)
    line2 =  (order_id, 'sku2', 10)
    line3 =  (order_id, 'sku3', 10)
    bus.handle(commands.CreateBatch(*batch1))
    bus.handle(commands.CreateBatch(*batch2))
    bus.handle(commands.CreateBatch(*batch3))
    bus.handle(commands.Allocate(*line1))
    bus.handle(commands.Allocate(*line2))
    bus.handle(commands.Allocate(*line3))
    allocations = bus.handle(queries.AllocationsForOrder(order_id))
    assert allocations == [
                            {'sku1': 'batch1'},
                            {'sku2': 'batch2'},
                            {'sku3': 'batch3'},
                          ]


@pytest.mark.django_db(transaction=True)
def test_deallocation_updates_batch_ref(tomorrow, bus):
    batch =  ('batch', 'sku', 10, tomorrow)
    line1 =  {'order_id': 'o1', 'sku': 'sku', 'qty': 5}
    line2 =  {'order_id': 'o2', 'sku': 'sku', 'qty': 5}
    bus.handle(commands.CreateBatch(*batch))
    bus.handle(commands.Allocate(**line1))
    bus.handle(commands.Allocate(**line2))
    bus.handle(commands.Deallocate(**line1))
    line1_batch_ref = bus.handle(queries.AllocationForLine(line1['order_id'], line1['sku']))
    assert line1_batch_ref is None
    line2_batch_ref = bus.handle(queries.AllocationForLine(line2['order_id'], line2['sku']))
    assert line2_batch_ref.decode() == 'batch'


@pytest.mark.django_db(transaction=True)
def test_deallocation_updates_order_allocations(tomorrow, bus):
    order_id = 'order1'
    batch1 =  ('batch1', 'sku1', 10, tomorrow)
    batch2 =  ('batch2', 'sku2', 10, tomorrow)
    batch3 =  ('batch3', 'sku3', 10, tomorrow)
    line1 =  (order_id, 'sku1', 10)
    line2 =  (order_id, 'sku2', 10)
    line3 =  (order_id, 'sku3', 10)
    bus.handle(commands.CreateBatch(*batch1))
    bus.handle(commands.CreateBatch(*batch2))
    bus.handle(commands.CreateBatch(*batch3))
    bus.handle(commands.Allocate(*line1))
    bus.handle(commands.Allocate(*line2))
    bus.handle(commands.Allocate(*line3))
    bus.handle(commands.Deallocate(*line2))
    allocations = bus.handle(queries.AllocationsForOrder(order_id))
    assert allocations == [
                            {'sku1': 'batch1'},
                            {'sku3': 'batch3'},
                          ]


@pytest.mark.django_db(transaction=True)
def test_changing_batch_quantity_updates_batch(today, bus):
    batch = {'ref': 'batch', 'sku': 'sku', 'qty': 10, 'eta': today}
    bus.handle(commands.CreateBatch(**batch))
    retrieved_batch = bus.handle(queries.BatchByRef(batch['ref']))
    assert retrieved_batch.qty == batch['qty']
    bus.handle(commands.ChangeBatchQuantity(batch['ref'], 5))
    retrieved_batch = bus.handle(queries.BatchByRef(batch['ref']))
    assert retrieved_batch.qty == 5
