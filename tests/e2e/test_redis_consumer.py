"""Tests for guaranteeing the redis consumer does its work."""
import json
import subprocess
from time import sleep
from redis.client import PubSub
from allocation.adapters.redis_publisher import redis_client
from allocation.entrypoints import redis_consumer
import pytest
import os


@pytest.fixture
def subscriber():
    return redis_client.pubsub(ignore_subscribe_messages=True)


@pytest.fixture
def consumer_process():
    consumer_relative_path = os.path.relpath(redis_consumer.__file__, os.getcwd())
    consumer_process = subprocess.Popen(['python', consumer_relative_path])
    sleep(0.5) # a little time for the subprocess to start
    return consumer_process


@pytest.mark.django_db(transaction=True)
def test_can_create_batch_using_redis_as_entrypoint(today, subscriber, consumer_process):
    subscriber.subscribe('create_batch')
    subscriber.subscribe('batch_created')

    batch = {
        'ref': 'batch',
        'sku': 'sku',
        'qty': 10,
        'eta': today.isoformat(),
    }
    json_batch = json.dumps(batch)
    redis_client.publish(channel='create_batch', message=json_batch)
    
    try:
        create_message = receive_message(subscriber)
        assert create_message['channel'] == 'create_batch'
        assert create_message['data'] == json_batch
        
        sleep(0.1) # let it process
        created_message = receive_message(subscriber)
        assert created_message['channel'] == 'batch_created'
        assert created_message['data'] == json_batch
    finally:
        consumer_process.terminate()
        consumer_process.wait()


@pytest.mark.django_db(transaction=True)
def test_can_allocate_a_line_using_redis_as_entrypoint(today, subscriber, consumer_process):
    subscriber.subscribe('line_allocated')

    batch = {
        'ref': 'batch',
        'sku': 'sku',
        'qty': 10,
        'eta': today.isoformat(),
    }
    line = {'order_id': 'o1', 'sku': 'sku', 'qty': 10}
    json_batch = json.dumps(batch)
    json_line = json.dumps(line)
    redis_client.publish(channel='create_batch', message=json_batch)
    redis_client.publish(channel='allocate_line', message=json_line)
    
    try:
        sleep(0.1) # let it process
        message = receive_message(subscriber)
        data = json.loads(message['data'])
        assert data['order_id'] == line['order_id']
        assert data['sku'] == line['sku']
        assert data['qty'] == line['qty']
        assert data['batch_ref'] == batch['ref']
    finally:
        consumer_process.terminate()
        consumer_process.wait()


@pytest.mark.django_db(transaction=True)
def test_can_allocate_a_line_using_redis_as_entrypoint(today, subscriber, consumer_process):
    subscriber.subscribe('line_deallocated')

    batch = {
        'ref': 'batch',
        'sku': 'sku',
        'qty': 10,
        'eta': today.isoformat(),
    }
    line = {'order_id': 'o1', 'sku': 'sku', 'qty': 10}
    json_batch = json.dumps(batch)
    json_line = json.dumps(line)
    redis_client.publish(channel='create_batch', message=json_batch)
    redis_client.publish(channel='allocate_line', message=json_line)
    redis_client.publish(channel='deallocate_line', message=json_line)
    
    try:
        sleep(0.1) # let it process
        message = receive_message(subscriber)
        data = json.loads(message['data'])
        assert data['order_id'] == line['order_id']
        assert data['sku'] == line['sku']
        assert data['qty'] == line['qty']
    finally:
        consumer_process.terminate()
        consumer_process.wait()


@pytest.mark.django_db(transaction=True)
def test_can_change_batch_quantity_using_redis_as_entrypoint(today, subscriber, consumer_process):
    subscriber.subscribe('line_deallocated')
    subscriber.subscribe('out_of_stock')

    batch = {
        'ref': 'batch',
        'sku': 'sku',
        'qty': 10,
        'eta': today.isoformat(),
    }
    line = {'order_id': 'o1', 'sku': 'sku', 'qty': 10}
    batch_change = {'ref': batch['ref'], 'qty': 5}
    json_batch = json.dumps(batch)
    json_line = json.dumps(line)
    json_batch_change = json.dumps(batch_change)
    redis_client.publish(channel='create_batch', message=json_batch)
    redis_client.publish(channel='allocate_line', message=json_line)
    redis_client.publish(channel='change_batch_quantity', message=json_batch_change)
    
    try:
        sleep(0.1) # let it process
        message = receive_message(subscriber)
        assert message['channel'] == 'line_deallocated'
        data = json.loads(message['data'])
        assert data['order_id'] == line['order_id']
        assert data['sku'] == line['sku']
        assert data['qty'] == line['qty']
        assert data['batch_ref'] == batch['ref']

        message = receive_message(subscriber)
        assert message['channel'] == 'out_of_stock'
        assert json.loads(message['data'])['sku'] == 'sku'

    finally:
        consumer_process.terminate()
        consumer_process.wait()


def test_redis_consumer_is_listening(subscriber: PubSub, consumer_process: subprocess.Popen[bytes]):
    
    subscriber.subscribe('consumer_pong')
    redis_client.publish('consumer_ping', 'ping')

    try:
        message = receive_message(subscriber)
        assert message['data'] == "pong"
    finally:
         consumer_process.terminate()
         consumer_process.wait()


def receive_message(subscriber):
        retries = 3
        while retries:
            message = subscriber.get_message()
            if message:
                return message
            sleep(0.3)
            retries -= 1
        else:
            raise AssertionError
