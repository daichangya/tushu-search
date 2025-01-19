#!/usr/bin/env python
import os
import sys

from sanic import Sanic
from sanic.response import html, redirect
from sanic_session import RedisSessionInterface

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tushu.config import CONFIG
from aiocache import caches

REDIS_DICT = CONFIG.REDIS_DICT
caches.set_config({
        "default": {
            "cache": "aiocache.backends.redis.RedisBackend",
            "endpoint": REDIS_DICT.get('REDIS_ENDPOINT', 'localhost'),
            "port": REDIS_DICT.get('REDIS_PORT', 6379),
            "db": REDIS_DICT.get('CACHE_DB', 0),
            "password": REDIS_DICT.get('REDIS_PASSWORD', None),
            "timeout": 10,
            "serializer": {
                "class": "aiocache.serializers.JsonSerializer"
            }
        }
    })

from tushu.views import admin_bp, api_bp, except_bp, md_bp, novels_bp,operate_bp
from tushu.database.redis import get_redis_async
from tushu.config import LOGGER, CONFIG

app = Sanic(__name__)
app.blueprint(md_bp)
app.blueprint(novels_bp)
app.blueprint(operate_bp)
app.blueprint(except_bp)
app.blueprint(admin_bp)
app.blueprint(api_bp)


@app.listener('before_server_start')
def init_cache(app, loop):
    # 配置 sanic_session 使用 Redis 存储会话
    # app.session_interface = RedisSessionInterface(redis_getter=redis_session.get_redis, prefix='session:')
    # Session(app, interface=session_interface)
    # redis instance for app
    # app.get_redis_pool = redis_session.get_redis_pool
    # pass the getter method for the connection pool into the session
    app.session_interface = RedisSessionInterface(
        get_redis_async, cookie_name="owl_sid", expiry=30 * 24 * 60 * 60)


@app.middleware('request')
async def add_session_to_request(request):
    # before each request initialize a session
    # using the client's request
    host = request.headers.get('host', None)
    user_agent = request.headers.get('user-agent', None)
    if user_agent:
        user_ip = request.headers.get('X-Forwarded-For')
        LOGGER.info('user ip is: {}'.format(user_ip))
        if user_ip in CONFIG.FORBIDDEN:
            return html("<h3>网站正在维护...</h3>")
        if CONFIG.VAL_HOST == 'true':
            if not host or host not in CONFIG.HOST:
                return redirect('http://www.owllook.net')
        if CONFIG.WEBSITE['IS_RUNNING']:
            await app.session_interface.open(request)
        else:
            return html("<h3>网站正在维护...</h3>")
    else:
        return html("<h3>网站正在维护...</h3>")


@app.middleware('response')
async def save_session(request, response):
    # after each request save the session,
    # pass the response to set client cookies
    # await app.session_interface.save(request, response)
    if request.path == '/operate/login' and request.ctx.session.get('user', None):
        await app.session_interface.save(request, response)
        import datetime
        response.cookies['owl_sid']['expires'] = datetime.datetime.now(
        ) + datetime.timedelta(days=30)
    elif request.path == '/register':
        try:
            response.cookies['reg_index'] = str(request.ctx.session['index'][0])
        except KeyError as e:
            LOGGER.error(e)


if __name__ == "__main__":
    workers = 1 if os.name == 'nt' else 2
    app.run(host="0.0.0.0", port=9200, debug=CONFIG.DEBUG)
