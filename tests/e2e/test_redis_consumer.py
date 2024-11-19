"""Tests for guaranteeing the redis consumer does its work."""
import json
from time import sleep
import pytest
from allocation.adapters.redis_channels import RedisChannels


@pytest.fixture(autouse=True)
def activate_redis_consumer(consumer_process):
    return


@pytest.fixture
def subscriber(redis_client):
    return redis_client.pubsub(ignore_subscribe_messages=True)


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
    subscriber.subscribe(RedisChannels.BATCH_CREATED)
    json_batch = json.dumps(batch)
    redis_client.publish(channel=RedisChannels.CREATE_BATCH, message=json_batch)
    created_message = receive_message(subscriber)
    assert created_message['data'] == json_batch


@pytest.mark.django_db(transaction=True)
def test_can_allocate_a_line_via_redis(batch, line, subscriber, redis_client):
    subscriber.subscribe(RedisChannels.LINE_ALLOCATED)
    json_batch = json.dumps(batch)
    json_line = json.dumps(line)
    redis_client.publish(channel=RedisChannels.CREATE_BATCH, message=json_batch)
    redis_client.publish(channel=RedisChannels.ALLOCATE_LINE, message=json_line)
    message = receive_message(subscriber)
    data = json.loads(message['data'])
    assert_line_fields_match(line, data)
    assert data['batch_ref'] == batch['ref']


@pytest.mark.django_db(transaction=True)
def test_can_deallocate_a_line_via_redis(batch, line, subscriber, redis_client):
    subscriber.subscribe(RedisChannels.LINE_DEALLOCATED)
    json_batch = json.dumps(batch)
    json_line = json.dumps(line)
    redis_client.publish(channel=RedisChannels.CREATE_BATCH, message=json_batch)
    redis_client.publish(channel=RedisChannels.ALLOCATE_LINE, message=json_line)
    redis_client.publish(channel=RedisChannels.DEALLOCATE_LINE, message=json_line)
    message = receive_message(subscriber)
    data = json.loads(message['data'])
    assert_line_fields_match(line, data)


@pytest.mark.django_db(transaction=True)
def test_can_change_batch_quantity_via_redis(batch, line, subscriber, redis_client):
    subscriber.subscribe(RedisChannels.LINE_DEALLOCATED)
    subscriber.subscribe(RedisChannels.OUT_OF_STOCK)
    subscriber.subscribe(RedisChannels.BATCH_QUANTITY_CHANGED)
    batch_change = {'ref': batch['ref'], 'qty': 5}
    json_batch = json.dumps(batch)
    json_line = json.dumps(line)
    json_batch_change = json.dumps(batch_change)
    redis_client.publish(channel=RedisChannels.CREATE_BATCH, message=json_batch)
    redis_client.publish(channel=RedisChannels.ALLOCATE_LINE, message=json_line)
    redis_client.publish(channel=RedisChannels.CHANGE_BATCH_QUANTITY, message=json_batch_change)
    
    message = receive_message(subscriber)
    assert message['channel'] == RedisChannels.LINE_DEALLOCATED
    data = json.loads(message['data'])
    assert_line_fields_match(line, data)
    assert data['batch_ref'] == batch['ref']

    message = receive_message(subscriber)
    assert message['channel'] == RedisChannels.BATCH_QUANTITY_CHANGED
    data = json.loads(message['data'])
    assert data['ref'] == batch_change['ref']
    assert data['qty'] == batch_change['qty']

    message = receive_message(subscriber)
    assert message['channel'] == RedisChannels.OUT_OF_STOCK
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
