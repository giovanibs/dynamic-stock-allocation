import os
from allocation.domain import events
from allocation.adapters.redis_query_repository import RedisQueryRepository
import redis


redis_client = redis.Redis(os.getenv('REDIS_HOST'), os.getenv('REDIS_PORT'))
redis_repo = RedisQueryRepository(os.getenv('REDIS_HOST'), os.getenv('REDIS_PORT'))


def add_batch(batch: events.BatchCreated, *args, **kwargs):
    redis_repo.add_batch(batch.ref, batch.sku, batch.qty, batch.eta)


def add_allocation(line: events.LineAllocated, *args, **kwargs):
    redis_repo.add_allocation_for_line(line.order_id, line.sku, line.batch_ref)


def add_order_allocation(line: events.LineAllocated, *args, **kwargs):
    redis_repo.add_allocation_for_order(line.order_id, line.sku, line.batch_ref)


def remove_allocation(line: events.LineDeallocated, *args, **kwargs):
    redis_repo.remove_allocation_for_line(line.order_id, line.sku)


def remove_allocations_for_order(line: events.LineDeallocated, *args, **kwargs):
    redis_repo.remove_allocation_for_order(line.order_id, line.sku)


def update_batch_quantity(batch: events.BatchQuantityChanged, *args, **kwargs):
    redis_repo.update_batch_quantity(batch.ref, batch.qty)
