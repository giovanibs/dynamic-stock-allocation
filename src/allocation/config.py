import os


def get_redis_config():
    return (
        os.getenv('REDIS_HOST', 'localhost'),
        os.getenv('REDIS_PORT', 6379)
    )
