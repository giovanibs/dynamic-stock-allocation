import django
django.setup()


# Ensure tests run correctly by migrating the in-memory database used by the
# `Consumer` when 'DJANGO_TEST_DATABASE' is set to True.
import os
from django.core.management import call_command

if os.getenv('DJANGO_TEST_DATABASE'):
    call_command('migrate')


import json
import logging
import redis
from typing import Dict

from allocation.domain import commands
from allocation.orchestration import message_bus
from allocation.orchestration.uow import DjangoUoW
from allocation.adapters.redis_channels import RedisChannels


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
        RedisChannels.CREATE_BATCH          : commands.CreateBatch,
        RedisChannels.ALLOCATE_LINE         : commands.Allocate,
        RedisChannels.DEALLOCATE_LINE       : commands.Deallocate,
        RedisChannels.CHANGE_BATCH_QUANTITY : commands.ChangeBatchQuantity,
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
