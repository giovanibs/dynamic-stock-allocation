import json
from time import sleep
import pytest
from allocation.adapters.redis_channels import RedisChannels as channels
from allocation.adapters.redis_query_repository import RedisQueryRepository


@pytest.fixture(autouse=True)
def activate_redis_consumer(consumer_process):
    return


@pytest.fixture
def redis_repo(redis_host, redis_port):
    return RedisQueryRepository(redis_host, redis_port)


def test_can_query_batch_by_ref(today, redis_client, redis_repo):
    batch = {
        'ref': 'batch',
        'sku': 'sku',
        'qty': 10,
        'eta': today.isoformat(),
    }
    redis_client.publish(channel=channels.CREATE_BATCH, message=json.dumps(batch))
    
    retries = 5
    while retries:
        retrieved_batch = redis_repo.get_batch(batch['ref'])

        if retrieved_batch:
            break

        sleep(0.5)
        retries -= 1
    
    assert retrieved_batch.ref == batch['ref']
    assert retrieved_batch.sku == batch['sku']
    assert retrieved_batch.qty == batch['qty']
    assert retrieved_batch.eta == batch['eta']


def test_can_query_batch_ref_for_allocation(today, redis_client, redis_repo):
    batch = {
        'ref': 'batch',
        'sku': 'sku',
        'qty': 10,
        'eta': today.isoformat(),
    }
    line = {'order_id': 'o1', 'sku': 'sku', 'qty': 10}
    redis_client.publish(channel=channels.CREATE_BATCH, message=json.dumps(batch))
    redis_client.publish(channel=channels.ALLOCATE_LINE, message=json.dumps(line))
    
    retries = 5
    while retries:
        batch_ref = redis_repo.allocation_for_line(line['order_id'], line['sku'])

        if batch_ref:
            break

        sleep(0.5)
        retries -= 1
    
    assert batch_ref.decode() == batch['ref']
