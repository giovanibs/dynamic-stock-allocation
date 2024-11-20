from allocation.adapters.redis_channels import RedisChannels
from allocation.domain import events
from allocation.domain.ports import AbstractPublisher
import dataclasses
import datetime
import json
import redis
from typing import Dict, Type


class DateEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.date):
            return o.isoformat()

        return super(DateEncoder, self).default(o)


class RedisEventPublisher(AbstractPublisher):
    
    CHANNELS: Dict[Type[events.Event], str] = {
            events.BatchCreated         : RedisChannels.BATCH_CREATED,
            events.BatchQuantityChanged : RedisChannels.BATCH_QUANTITY_CHANGED,
            events.LineAllocated        : RedisChannels.LINE_ALLOCATED,
            events.LineDeallocated      : RedisChannels.LINE_DEALLOCATED,
            events.OutOfStock           : RedisChannels.OUT_OF_STOCK,
        }
    
    
    def __init__(self, redis_host, redis_port) -> None:
        self._client: redis.Redis = redis.Redis(redis_host, redis_port)

    
    def publish_event(self, event: events.Event):
        self._client.publish(
            channel=self.CHANNELS[type(event)],
            message=json.dumps(dataclasses.asdict(event), cls=DateEncoder)
        )
