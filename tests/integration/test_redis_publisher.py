import json
from time import sleep
import pytest
from allocation.adapters.redis_channels import RedisChannels
from allocation.adapters.redis_publisher import RedisEventPublisher
from allocation.domain import commands
from allocation.domain.exceptions import OutOfStock
from allocation.orchestration import bootstrapper


@pytest.fixture
def bus(redis_host, redis_port):
    return bootstrapper.bootstrap(
        publisher=RedisEventPublisher(redis_host, redis_port)
    )


@pytest.fixture
def batch(tomorrow) -> tuple:
    return ('batch', 'skew', 10, tomorrow)


@pytest.fixture
def subscriber(redis_client):
    return redis_client.pubsub(ignore_subscribe_messages=True)


class TestRedisPublishesEvents:

    @pytest.mark.django_db(transaction=True)
    def test_redis_publishes_batch_created(self, subscriber, batch, bus):
        subscriber.subscribe(RedisChannels.BATCH_CREATED)
        bus.handle(commands.CreateBatch(*batch))
        message = self.receive_message(subscriber)
        assert message['channel'] == RedisChannels.BATCH_CREATED
        assert json.loads(message['data'])['ref'] == batch[0]
        assert json.loads(message['data'])['sku'] == batch[1]
        assert json.loads(message['data'])['qty'] == batch[2]
        assert json.loads(message['data'])['eta'] == batch[3].isoformat()

        
    @pytest.mark.django_db(transaction=True)
    def test_redis_publishes_line_allocated(self, subscriber, batch, bus):
        subscriber.subscribe(RedisChannels.LINE_ALLOCATED)
        line = ('o1', 'skew', 1)
        bus.handle(commands.CreateBatch(*batch))
        bus.handle(commands.Allocate(*line))
        message = self.receive_message(subscriber)
        assert message['channel'] == RedisChannels.LINE_ALLOCATED
        assert json.loads(message['data'])['order_id'] == line[0]
        assert json.loads(message['data'])['sku'] == line[1]
        assert json.loads(message['data'])['qty'] == line[2]
        assert json.loads(message['data'])['batch_ref'] == batch[0]


    @pytest.mark.django_db(transaction=True)
    def test_redis_publishes_line_deallocated(self, subscriber, batch, bus):
        subscriber.subscribe(RedisChannels.LINE_DEALLOCATED)
        line = ('o1', 'skew', 1)
        bus.handle(commands.CreateBatch(*batch))
        bus.handle(commands.Allocate(*line))
        bus.handle(commands.Deallocate(*line))
        message = self.receive_message(subscriber)
        assert message['channel'] == RedisChannels.LINE_DEALLOCATED
        assert json.loads(message['data'])['order_id'] == line[0]
        assert json.loads(message['data'])['sku'] == line[1]
        assert json.loads(message['data'])['qty'] == line[2]


    @pytest.mark.django_db(transaction=True)
    def test_redis_publishes_out_of_stock(self, subscriber, batch, bus):
        subscriber.subscribe(RedisChannels.OUT_OF_STOCK)
        line = ('o1', 'skew', batch[2] + 1)
        bus.handle(commands.CreateBatch(*batch))
        with pytest.raises(OutOfStock):
            bus.handle(commands.Allocate(*line))
        message = self.receive_message(subscriber)
        assert message['channel'] == RedisChannels.OUT_OF_STOCK
        assert json.loads(message['data'])['sku'] == 'skew'

    
    @pytest.mark.django_db(transaction=True)
    def test_redis_publishes_batch_changed(self, subscriber, batch, bus):
        subscriber.subscribe(RedisChannels.BATCH_QUANTITY_CHANGED)
        line = ('o1', 'skew', batch[2])
        bus.handle(commands.CreateBatch(*batch))
        bus.handle(commands.Allocate(*line))
        with pytest.raises(OutOfStock):
            bus.handle(commands.ChangeBatchQuantity(batch[0], batch[2] - 1))
        message = self.receive_message(subscriber)
        assert message['channel'] == RedisChannels.BATCH_QUANTITY_CHANGED
        assert json.loads(message['data'])['ref'] == batch[0]
        assert json.loads(message['data'])['qty'] == batch[2] - 1


    @staticmethod
    def receive_message(subscriber):
        retries = 5
        while retries:
            message = subscriber.get_message()
            if message:
                return message
            sleep(0.3)
            retries -= 1
        else:
            raise AssertionError
