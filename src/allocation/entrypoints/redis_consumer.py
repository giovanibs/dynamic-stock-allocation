import django
django.setup()


# Ensure tests run correctly by migrating the in-memory database used by the
# `Consumer` when 'DJANGO_TEST_DATABASE' is set to True.
import os
from django.core.management import call_command

if os.getenv('DJANGO_TEST_DATABASE'):
    call_command('migrate')


import json
import redis
from typing import Dict

from allocation.config import get_logger, get_redis_config
from allocation.domain import commands
from allocation.orchestration import message_bus
from allocation.orchestration.uow import DjangoUoW
from allocation.adapters.redis_channels import RedisChannels


logger = get_logger()
redis_config = get_redis_config()
redis_client = redis.Redis(redis_config[0], redis_config[1], decode_responses=True)

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
