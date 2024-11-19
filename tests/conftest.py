import os
import subprocess
from time import sleep
import pytest
import redis
from datetime import date, timedelta
from allocation.entrypoints import redis_consumer


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
    return os.getenv('REDIS_HOST')


@pytest.fixture(scope="session")
def redis_port():
    return os.getenv('REDIS_PORT')


@pytest.fixture(scope="session")
def redis_client(redis_host, redis_port):
    yield redis.Redis(host=redis_host, port=redis_port, decode_responses=True)


@pytest.fixture(scope="function", autouse=True)
def clear_redis(redis_client):
    redis_client.flushall()
    yield
    redis_client.flushall()


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
