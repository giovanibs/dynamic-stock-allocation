import os
import subprocess
from time import sleep
import pytest
import redis
from datetime import date, timedelta
from allocation.config import get_redis_config
from allocation.entrypoints import redis_consumer
from allocation.orchestration.uow import DjangoUoW


@pytest.fixture(scope='session')
def today():
    return date.today()


@pytest.fixture(scope='session')
def tomorrow(today):
    return today + timedelta(days=1)


@pytest.fixture(scope='session')
def later(today):
    return today + timedelta(days=2)


@pytest.fixture(scope="session")
def redis_host():
    return get_redis_config()[0]


@pytest.fixture(scope="session")
def redis_port():
    return get_redis_config()[1]


@pytest.fixture(scope="session")
def redis_client(redis_host, redis_port):
    yield redis.Redis(host=redis_host, port=redis_port, decode_responses=True)


@pytest.fixture(scope='module')
def consumer_process():
    env = os.environ.copy()
    env['DJANGO_TEST_DATABASE'] = '1'
    consumer_relative_path = os.path.relpath(redis_consumer.__file__, os.getcwd())
    consumer_process = subprocess.Popen(['python', consumer_relative_path], env=env)
    sleep(1) # a little time for the subprocess to start and migrate the database
    
    yield consumer_process

    consumer_process.terminate()
    consumer_process.wait()


@pytest.fixture(scope='function')
def django_uow():
    return DjangoUoW()
