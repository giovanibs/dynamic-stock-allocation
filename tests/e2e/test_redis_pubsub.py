""" TEMPORARY TEST FILE TO TRY OUT REDIS PUBSUB"""
from time import sleep
import redis
from dotenv import load_dotenv
import os

load_dotenv()
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')


def test_you_speak_and_i_listen():
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    pub = redis_client
    channel = 'test'
    msg = 'testing...'
    sub = redis_client.pubsub()
    sub.subscribe({channel: lambda msg: msg})
    pub.publish(channel, msg)
    
    retries = 3
    while retries:
        received = sub.get_message(ignore_subscribe_messages=True, timeout=1)
        if received:
            break
        sleep(0.5)
        retries -= 1
    
    assert received['data'] == msg
