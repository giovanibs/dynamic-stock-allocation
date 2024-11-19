import json
from time import sleep
import pytest
from allocation.domain import commands
from allocation.orchestration.uow import DjangoUoW
from allocation.orchestration.message_bus import MessageBus


@pytest.fixture
def uow() -> DjangoUoW:
    return DjangoUoW()


@pytest.fixture
def batch(tomorrow) -> tuple:
    return ('batch', 'skew', 10, tomorrow)


@pytest.fixture
def subscriber(redis_client):
    return redis_client.pubsub(ignore_subscribe_messages=True)


class TestRedisPublishesEvents:

    @pytest.mark.django_db(transaction=True)
    def test_redis_publishes_batch_created(self, subscriber, batch, uow):
        subscriber.subscribe('batch_created')
        MessageBus.handle(commands.CreateBatch(*batch), uow)
        message = self.receive_message(subscriber)
        assert message['channel'] == 'batch_created'
        assert json.loads(message['data'])['ref'] == batch[0]
        assert json.loads(message['data'])['sku'] == batch[1]
        assert json.loads(message['data'])['qty'] == batch[2]
        assert json.loads(message['data'])['eta'] == batch[3].isoformat()

        
    @pytest.mark.django_db(transaction=True)
    def test_redis_publishes_line_allocated(self, subscriber, batch, uow):
        subscriber.subscribe('line_allocated')
        line = ('o1', 'skew', 1)
        MessageBus.handle(commands.CreateBatch(*batch), uow)
        MessageBus.handle(commands.Allocate(*line), uow)
        message = self.receive_message(subscriber)
        assert message['channel'] == 'line_allocated'
        assert json.loads(message['data'])['order_id'] == line[0]
        assert json.loads(message['data'])['sku'] == line[1]
        assert json.loads(message['data'])['qty'] == line[2]
        assert json.loads(message['data'])['batch_ref'] == batch[0]


    @pytest.mark.django_db(transaction=True)
    def test_redis_publishes_line_deallocated(self, subscriber, batch, uow):
        subscriber.subscribe('line_deallocated')
        line = ('o1', 'skew', 1)
        MessageBus.handle(commands.CreateBatch(*batch), uow)
        MessageBus.handle(commands.Allocate(*line), uow)
        MessageBus.handle(commands.Deallocate(*line), uow)
        message = self.receive_message(subscriber)
        assert message['channel'] == 'line_deallocated'
        assert json.loads(message['data'])['order_id'] == line[0]
        assert json.loads(message['data'])['sku'] == line[1]
        assert json.loads(message['data'])['qty'] == line[2]


    @pytest.mark.django_db(transaction=True)
    def test_redis_publishes_out_of_stock(self, subscriber, batch, uow):
        subscriber.subscribe('out_of_stock')
        line = ('o1', 'skew', batch[2] + 1)
        MessageBus.handle(commands.CreateBatch(*batch), uow)
        MessageBus.handle(commands.Allocate(*line), uow)
        message = self.receive_message(subscriber)
        assert message['channel'] == 'out_of_stock'
        assert json.loads(message['data'])['sku'] == 'skew'

    
    @pytest.mark.django_db(transaction=True)
    def test_redis_publishes_batch_changed(self, subscriber, batch, uow):
        subscriber.subscribe('batch_quantity_changed')
        line = ('o1', 'skew', batch[2])
        MessageBus.handle(commands.CreateBatch(*batch), uow)
        MessageBus.handle(commands.Allocate(*line), uow)
        MessageBus.handle(commands.ChangeBatchQuantity(batch[0], batch[2] - 1), uow)
        message = self.receive_message(subscriber)
        assert message['channel'] == 'batch_quantity_changed'
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
