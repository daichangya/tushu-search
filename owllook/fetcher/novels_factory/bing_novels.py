#!/usr/bin/env python
"""
 Created by howie.hu at 2018/5/28.
"""
import asyncio
import urllib

from aiocache.serializers import PickleSerializer
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from aiocache import caches, cached
from owllook.fetcher.function import get_random_user_agent
from owllook.fetcher.novels_factory.base_novels import BaseNovels


class BingNovels(BaseNovels):

    def __init__(self):
        super(BingNovels, self).__init__()

    async def data_extraction(self, html):
        """
        小说信息抓取函数
        :return:
        """
        try:
            title = html.select('h2 a')[0].get_text()
            url = html.select('h2 a')[0].get('href', None)
            netloc = urlparse(url).netloc
            url = url.replace('index.html', '').replace('Index.html', '')
            if not url or 'qidian.com' in url or 'qq.com' in url or 'baidu' in url or 'baike.so.com' in url or netloc in self.black_domain or '.html' in url:
                return None
            is_parse = 1 if netloc in self.rules.keys() else 0
            is_recommend = 1 if netloc in self.latest_rules.keys() else 0
            timestamp = 0
            time = ''
            return {'title': title,
                    'url': url,
                    'time': time,
                    'is_parse': is_parse,
                    'is_recommend': is_recommend,
                    'timestamp': timestamp,
                    'netloc': netloc}

        except Exception as e:
            self.logger.exception(e)
            return None

    async def novels_search(self, novels_name):
        """
        小说搜索入口函数
        :return:
        """
        # url = self.config.BY_URL
        # headers = {
        #     'user-agent': await get_random_user_agent(),
        #     'referer': "https://cn.bing.com/"
        # }
        # params = {'q': novels_name, 'count': 20}
        # query_encoded = urllib.parse.quote_plus(novels_name)
        url = f"https://cn.bing.com/search?q={novels_name}&count=20"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/113.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        html = await self.fetch_url(url=url, params=None, headers=headers)
        if html:
            soup = BeautifulSoup(html, 'html5lib')
            result = soup.find_all(class_='b_algo')
            extra_tasks = [self.data_extraction(html=i) for i in result]
            tasks = [asyncio.ensure_future(i) for i in extra_tasks]
            done_list, pending_list = await asyncio.wait(tasks)
            res = [task.result() for task in done_list if task.result()]
            return res
        else:
            return []


@cached(ttl=259200,  serializer=PickleSerializer(), namespace="novels_name")
async def start(novels_name):
    """
    Start spider
    :return:
    """
    return await BingNovels.start(novels_name)


if __name__ == '__main__':
    # Start
    import aiocache

    REDIS_DICT = {}
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
    res = asyncio.get_event_loop().run_until_complete(start('肝出个大器晚成 小说 阅读 最新章节'))
    for i in res:
        print(i)
