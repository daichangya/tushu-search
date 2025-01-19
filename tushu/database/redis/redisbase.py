#!/usr/bin/env python
import aioredis
from aiocache import caches
from tushu.config import CONFIG

REDIS_DICT = CONFIG.REDIS_DICT


# Token from https://github.com/subyraman/sanic_session
def get_redis():
    return caches.get('default')

async def get_redis_async():
    # 假设这里是一些异步操作，比如连接 Redis 服务器
    # 例如使用 aioredis 库
    host = REDIS_DICT.get('REDIS_ENDPOINT', 'localhost')
    port = REDIS_DICT.get('REDIS_PORT', 6379)
    password = REDIS_DICT.get('REDIS_PASSWORD', None)
    db = REDIS_DICT.get('CACHE_DB', 0)
    redis_url = f"redis://{host}:{port}/{db}"
    if password:
        redis_url = f"redis://:{password}@{host}:{port}/{db}"

    redis = aioredis.Redis.from_url(
        redis_url, max_connections=10, decode_responses=True
    )
    return redis