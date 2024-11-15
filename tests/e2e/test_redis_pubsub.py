""" TEMPORARY TEST FILE TO TRY OUT REDIS PUBSUB"""
from datetime import date
from time import sleep
from typing import Optional
from django.test import Client
import pytest
import redis
from dotenv import load_dotenv
import os
from allocation.domain import commands
from allocation.orchestration.message_bus import MessageBus
from allocation.orchestration.uow import DjangoUoW


load_dotenv()
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
uow = DjangoUoW()


@pytest.mark.django_db(transaction=True)
def test_changing_batch_quantity_publishes_reallocation_when_needed(later):
    subscriber = redis_client.pubsub()
    subscriber.subscribe({'reallocation': lambda msg: msg})
    post_to_create_batch('earlier', 'sku', 10)
    post_to_create_batch('later', 'sku', 10, later)
    order_id = 'o1'
    batch = post_to_allocate_line(order_id, 'sku', 10)['batch_ref']
    assert batch == 'earlier'
    MessageBus.handle(commands.ChangeBatchQuantity('earlier', 5), uow)
    
    retries = 3
    while retries:
        received = subscriber.get_message(ignore_subscribe_messages=True, timeout=1)
        if received:
            break
        sleep(0.1)
        retries -= 1
    else:
        raise AssertionError
    
    assert received['data'] == order_id


def post_to_create_batch(ref: str, sku: str, qty: int, eta: Optional[date]=None) -> dict:
    response = Client().post(
        path = '/api/batches',
        data = {'ref': ref,'sku': sku,'qty': qty,'eta': eta},
        content_type = "application/json"
    )
    assert response.status_code == 201
    return response.json()


def post_to_allocate_line(order_id: str, sku: str, qty: int) -> dict:
    response = Client().post(
        path = '/api/allocate',
        data = {'order_id': order_id, 'sku': sku, 'qty': qty},
        content_type = "application/json"
    )
    assert response.status_code == 201
    return response.json()
