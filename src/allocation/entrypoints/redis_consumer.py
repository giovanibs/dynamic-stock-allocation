import os
import redis

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def main():
    subscriber = redis_client.pubsub(ignore_subscribe_messages=True)
    subscriber.subscribe('consumer_ping')
    event_listener(subscriber)


def event_listener(subscriber):
    for _ in subscriber.listen():
        redis_client.publish('consumer_pong', 'pong')


if __name__ == '__main__':
    main()
