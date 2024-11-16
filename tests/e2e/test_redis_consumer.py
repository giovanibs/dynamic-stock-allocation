"""Tests for guaranteeing the redis consumer does its work."""
import subprocess
from time import sleep
from allocation.adapters.redis_publisher import redis_client
from allocation.entrypoints import redis_consumer
import pytest
import os


@pytest.fixture
def subscriber():
    return redis_client.pubsub(ignore_subscribe_messages=True)


def test_redis_consumer_is_listening(subscriber):
    consumer_relative_path = os.path.relpath(redis_consumer.__file__, os.getcwd())
    consumer_process = subprocess.Popen(['python', consumer_relative_path])
    sleep(0.5) # a little time for the subprocess to start
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
