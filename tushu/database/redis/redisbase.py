#!/usr/bin/env python
import aioredis

from tushu.config import CONFIG


# Token from https://github.com/subyraman/sanic_session
class RedisSession:

    async def get_redis(self):

        REDIS_DICT = CONFIG.REDIS_DICT
        host = REDIS_DICT.get('REDIS_ENDPOINT', "localhost")
        port = REDIS_DICT.get('REDIS_PORT', 6379)
        poolsize = REDIS_DICT.get('POOLSIZE', 10)
        password = REDIS_DICT.get('REDIS_PASSWORD', None)
        db = REDIS_DICT.get('SESSION_DB', None)
        # 动态生成Redis连接URL
        url = f"redis://{host}:{port}"
        # 创建连接池
        redis = await aioredis.Redis.from_url(
            url,
            decode_responses=True,
            max_connections=poolsize,
            password=password,
            db=db
        )
        return redis
