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
from allocation.orchestration import bootstrapper
from allocation.adapters.redis_channels import RedisChannels
from allocation.domain.exceptions import DomainException, ValidationError


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
    subscriber.subscribe(RedisChannels.CONSUMER_PING)
    
    for channel in CHANNEL_COMMAND_MAP:
        subscriber.subscribe(channel)
    
    event_listener(subscriber)


def event_listener(subscriber):
    
    for msg in subscriber.listen():
        
        if msg['channel'] == RedisChannels.CONSUMER_PING:
            redis_client.publish(RedisChannels.CONSUMER_PONG, 1)
            continue

        data = json.loads(msg['data'])
        bus = bootstrapper.bootstrap()
        try:
            bus.handle(CHANNEL_COMMAND_MAP[msg['channel']](**data))
        except DomainException:
            logger.exception('DomainException')
        except ValidationError:
            logger.exception('ValidationError')
        except Exception as e:
            logger.exception('Other exception')


if __name__ == '__main__':
    main()
