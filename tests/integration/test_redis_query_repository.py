import json
import os
import subprocess
from time import sleep
import pytest
from allocation.adapters.redis_query_repository import RedisQueryRepository
from allocation.entrypoints import redis_consumer


@pytest.fixture(scope='module', autouse=True)
def consumer_process():
    consumer_relative_path = os.path.relpath(redis_consumer.__file__, os.getcwd())
    consumer_process = subprocess.Popen(['python', consumer_relative_path])
    sleep(0.5) # a little time for the subprocess to start
    
    yield consumer_process

    consumer_process.terminate()
    consumer_process.wait()


@pytest.fixture
def redis_repo(redis_host, redis_port):
    return RedisQueryRepository(redis_host, redis_port)


@pytest.mark.django_db(transaction=True)
def test_can_query_batch_by_ref(today, redis_client, redis_repo):
    batch = {
        'ref': 'batch',
        'sku': 'sku',
        'qty': 10,
        'eta': today.isoformat(),
    }
    redis_client.publish(channel='create_batch', message=json.dumps(batch))
    
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