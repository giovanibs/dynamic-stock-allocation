from allocation.adapters.redis_channels import RedisChannels
from allocation.domain import events
import dataclasses
import datetime
import json
import os
import redis
from typing import Dict, Type


REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


class DateEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.date):
            return o.isoformat()

        return super(DateEncoder, self).default(o)


class RedisEventPublisher:
    
    CHANNELS: Dict[Type[events.Event], str] = {
            events.BatchCreated         : RedisChannels.BATCH_CREATED,
            events.BatchQuantityChanged : RedisChannels.BATCH_QUANTITY_CHANGED,
            events.LineAllocated        : RedisChannels.LINE_ALLOCATED,
            events.LineDeallocated      : RedisChannels.LINE_DEALLOCATED,
            events.OutOfStock           : RedisChannels.OUT_OF_STOCK,
        }
    
    
    def __init__(self, redis_client: redis.Redis) -> None:
        self._redis_client = redis_client

    
    def publish_event(self, event: events.Event):
        self._redis_client.publish(
            channel=self.CHANNELS[type(event)],
            message=json.dumps(dataclasses.asdict(event), cls=DateEncoder)
        )
