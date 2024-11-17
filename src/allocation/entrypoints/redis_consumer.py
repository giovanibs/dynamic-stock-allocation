import django
django.setup()

import json
import logging
import os
import redis

from allocation.domain import commands
from allocation.orchestration import message_bus
from allocation.orchestration.uow import DjangoUoW


logger = logging.getLogger(__name__)

if logger.hasHandlers():
    logger.handlers.clear()

filename = os.path.join(os.getcwd(), 'logs.log')
file_handler = logging.FileHandler(filename, mode='a')
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def main():
    logger.debug('Starting redis consumer')
    subscriber = redis_client.pubsub(ignore_subscribe_messages=True)
    
    channels = [
        'consumer_ping',
        'create_batch',
        'allocate_line',
        'deallocate_line'
    ]
    for channel in channels:
        subscriber.subscribe(channel)
    
    try:
        event_listener(subscriber)
    except:
        logger.exception('Error while listening...')


def event_listener(subscriber):
    for msg in subscriber.listen():

        if msg['channel'] == 'consumer_ping':
            redis_client.publish('consumer_pong', 'pong')

        elif msg['channel'] == 'create_batch':
            batch_data = json.loads(msg['data'])
            message_bus.MessageBus.handle(
                commands.CreateBatch(**batch_data),
                DjangoUoW()
            )
        elif msg['channel'] == 'allocate_line':
            line_data = json.loads(msg['data'])
            message_bus.MessageBus.handle(
                commands.Allocate(**line_data),
                DjangoUoW()
            )
        elif msg['channel'] == 'deallocate_line':
            line_data = json.loads(msg['data'])
            message_bus.MessageBus.handle(
                commands.Deallocate(**line_data),
                DjangoUoW()
            )

if __name__ == '__main__':
    main()
