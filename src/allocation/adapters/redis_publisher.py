from allocation.adapters.redis_channels import RedisChannels
from allocation.config import get_redis_config
from allocation.domain import events
import dataclasses
import datetime
import json
import redis
from typing import Dict, Type


redis_config = get_redis_config()
redis_client = redis.Redis(redis_config[0], redis_config[1], decode_responses=True)


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
