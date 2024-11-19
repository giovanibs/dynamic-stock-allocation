import redis
from allocation.domain.ports import AbstractQueryRepository
import pickle


class RedisQueryRepository(AbstractQueryRepository):
    
    def __init__(self, redis_host, redis_port) -> None:
        self._client: redis.Redis = redis.Redis(redis_host, redis_port)
    
    
    def get_batch(self, ref: str):
        batch_data = self._client.hget('batches', ref)
        return pickle.loads(batch_data) if batch_data else None
        