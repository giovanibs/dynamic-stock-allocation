import django
django.setup()

import json
import logging
import os
import redis
from typing import Dict

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

CHANNEL_COMMAND_MAP: Dict[str, commands.Command] = {
        'create_batch'          : commands.CreateBatch,
        'allocate_line'         : commands.Allocate,
        'deallocate_line'       : commands.Deallocate,
        'change_batch_quantity' : commands.ChangeBatchQuantity,
    }


def main():
    subscriber = redis_client.pubsub(ignore_subscribe_messages=True)
    
    for channel in CHANNEL_COMMAND_MAP:
        subscriber.subscribe(channel)
    
    try:
        event_listener(subscriber)
    except:
        logger.exception('Error while listening...')


def event_listener(subscriber):
    for msg in subscriber.listen():
        data = json.loads(msg['data'])
        message_bus.MessageBus.handle(
            CHANNEL_COMMAND_MAP[msg['channel']](**data),
            DjangoUoW()
        )


if __name__ == '__main__':
    main()
