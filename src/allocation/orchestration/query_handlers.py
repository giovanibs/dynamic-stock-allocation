from allocation.config import get_redis_config
from allocation.domain import events
from allocation.adapters.redis_query_repository import RedisQueryRepository


redis_config = get_redis_config()
redis_repo = RedisQueryRepository(redis_config[0], redis_config[1])


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
