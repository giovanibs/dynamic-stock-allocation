"""Tests for guaranteeing the redis consumer does its work."""
import json
import subprocess
from time import sleep
from allocation.entrypoints import redis_consumer
import pytest
import os


@pytest.fixture
def subscriber(redis_client):
    return redis_client.pubsub(ignore_subscribe_messages=True)


@pytest.fixture(scope='module', autouse=True)
def consumer_process():
    consumer_relative_path = os.path.relpath(redis_consumer.__file__, os.getcwd())
    consumer_process = subprocess.Popen(['python', consumer_relative_path])
    sleep(0.5) # a little time for the subprocess to start
    
    yield consumer_process

    consumer_process.terminate()
    consumer_process.wait()


@pytest.fixture
def batch(today):
    return {
        'ref': 'batch',
        'sku': 'sku',
        'qty': 10,
        'eta': today.isoformat(),
    }


@pytest.fixture
def line():
    return {'order_id': 'o1', 'sku': 'sku', 'qty': 10}


@pytest.mark.django_db(transaction=True)
def test_can_create_batch_via_redis(batch, subscriber, redis_client):
    subscriber.subscribe('batch_created')
    json_batch = json.dumps(batch)
    redis_client.publish(channel='create_batch', message=json_batch)
    created_message = receive_message(subscriber)
    assert created_message['data'] == json_batch


@pytest.mark.django_db(transaction=True)
def test_can_allocate_a_line_via_redis(batch, line, subscriber, redis_client):
    subscriber.subscribe('line_allocated')
    json_batch = json.dumps(batch)
    json_line = json.dumps(line)
    redis_client.publish(channel='create_batch', message=json_batch)
    redis_client.publish(channel='allocate_line', message=json_line)
    message = receive_message(subscriber)
    data = json.loads(message['data'])
    assert_line_fields_match(line, data)
    assert data['batch_ref'] == batch['ref']


@pytest.mark.django_db(transaction=True)
def test_can_deallocate_a_line_via_redis(batch, line, subscriber, redis_client):
    subscriber.subscribe('line_deallocated')
    json_batch = json.dumps(batch)
    json_line = json.dumps(line)
    redis_client.publish(channel='create_batch', message=json_batch)
    redis_client.publish(channel='allocate_line', message=json_line)
    redis_client.publish(channel='deallocate_line', message=json_line)
    message = receive_message(subscriber)
    data = json.loads(message['data'])
    assert_line_fields_match(line, data)


@pytest.mark.django_db(transaction=True)
def test_can_change_batch_quantity_via_redis(batch, line, subscriber, redis_client):
    subscriber.subscribe('line_deallocated')
    subscriber.subscribe('out_of_stock')
    subscriber.subscribe('batch_quantity_changed')
    batch_change = {'ref': batch['ref'], 'qty': 5}
    json_batch = json.dumps(batch)
    json_line = json.dumps(line)
    json_batch_change = json.dumps(batch_change)
    redis_client.publish(channel='create_batch', message=json_batch)
    redis_client.publish(channel='allocate_line', message=json_line)
    redis_client.publish(channel='change_batch_quantity', message=json_batch_change)
    
    message = receive_message(subscriber)
    assert message['channel'] == 'line_deallocated'
    data = json.loads(message['data'])
    assert_line_fields_match(line, data)
    assert data['batch_ref'] == batch['ref']

    message = receive_message(subscriber)
    assert message['channel'] == 'batch_quantity_changed'
    data = json.loads(message['data'])
    assert data['ref'] == batch_change['ref']
    assert data['qty'] == batch_change['qty']

    message = receive_message(subscriber)
    assert message['channel'] == 'out_of_stock'
    assert json.loads(message['data'])['sku'] == 'sku'


def assert_line_fields_match(line, data):
    assert data['order_id'] == line['order_id']
    assert data['sku'] == line['sku']
    assert data['qty'] == line['qty']


def receive_message(subscriber):
    retries = 5
    while retries:
        message = subscriber.get_message()
        if message:
            return message
        sleep(0.3)
        retries -= 1
    else:
        raise AssertionError
