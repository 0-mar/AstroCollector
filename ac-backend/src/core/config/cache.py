from aiocache import caches

caches.set_config(
    {
        "default": {
            "cache": "aiocache.RedisCache",
            "endpoint": "localhost",
            "port": 6379,
            "timeout": 1,
            "serializer": {"class": "aiocache.serializers.PickleSerializer"},
        }
    }
)
