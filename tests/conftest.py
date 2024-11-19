import os
import pytest
import redis

from datetime import date, timedelta


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
