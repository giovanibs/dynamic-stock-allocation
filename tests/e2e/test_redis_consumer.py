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
