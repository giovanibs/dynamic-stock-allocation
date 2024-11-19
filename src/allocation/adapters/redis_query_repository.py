import redis
from allocation.domain import model as domain_
from allocation.domain.ports import AbstractQueryRepository


class RedisQueryRepository(AbstractQueryRepository):
    
    def __init__(self, redis_client) -> None:
        self._client: redis.Redis = redis_client
    
    
    def get_batch(self, ref: str):
        batch_data = self._client.hgetall(f'batch:{ref}')
        return domain_.Batch(
            batch_data['ref'],
            batch_data['sku'],
            int(batch_data['qty']),
            batch_data['eta'],
            ) \
            if batch_data else None
        