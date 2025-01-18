#!/usr/bin/env python
"""
 Created by howie.hu at 2018/5/28.
"""
import urllib

from aiocache import caches, cached
import asyncio
import async_timeout
import requests

from aiocache.serializers import PickleSerializer
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from aiocache import cached
from owllook.fetcher.function import get_random_user_agent
from owllook.fetcher.novels_factory.base_novels import BaseNovels


class BaiduNovels(BaseNovels):

    def __init__(self):
        super(BaiduNovels, self).__init__()

    async def data_extraction(self, html):
        """
        小说信息抓取函数
        :return:
        """
        try:
            url = html.select('h3.t a')[0].get('href', None)
            real_url = await self.get_real_url(url=url) if url else None
            if real_url:
                real_str_url = str(real_url)
                netloc = urlparse(real_str_url).netloc
                if "http://" + netloc + "/" == real_str_url:
                    return None
                if (not real_url or 'qidian.com' in real_url or 'qq.com' in real_url or 'baidu' in real_url or 'baike.so.com' in real_url
                        or netloc in self.black_domain):
                    return None
                is_parse = 1 if netloc in self.rules.keys() else 0
                title = html.select('h3.t a')[0].get_text()
                is_recommend = 1 if netloc in self.latest_rules.keys() else 0
                # time = re.findall(r'\d+-\d+-\d+', source)
                # time = time[0] if time else None
                timestamp = 0
                time = ""
                return {'title': title, 'url': real_str_url.replace('index.html', ''), 'time': time,
                        'is_parse': is_parse,
                        'is_recommend': is_recommend,
                        'timestamp': timestamp,
                        'netloc': netloc}
            else:
                return None
        except Exception as e:
            self.logger.exception(e)
            return None

    async def get_real_url(self, url):
        """
        获取百度搜索结果真实url
        :param url:
        :return:
        """
        try:
            headers = {'user-agent': await get_random_user_agent()}
            response = requests.head(url, params=None, headers=headers,allow_redirects=True, timeout=20)
            self.logger.info('Parse url: {}'.format(response.url))
            url = response.url if response.url else None
            return url
        except requests.RequestException as e:
            raise Exception(f"请求百度失败：{e}")
        except Exception as e:
            raise Exception(f"解码百度搜索结果页面失败：{e}")

        # with async_timeout.timeout(5):
        #     try:
        #         async with aiohttp.ClientSession() as client:
        #             headers = {'user-agent': await get_random_user_agent()}
        #             async with client.head(url, headers=headers, allow_redirects=True) as response:
        #                 self.logger.info('Parse url: {}'.format(response.url))
        #                 url = response.url if response.url else None
        #                 return url
        #     except Exception as e:
        #         self.logger.exception(e)
        #         return None

    async def novels_search(self, novels_name):
        """
        小说搜索入口函数
        :return:
        """
        query_encoded = urllib.parse.quote_plus(novels_name)
        url = f"https://www.baidu.com/s?wd={query_encoded}&rn=20&ie=utf-8"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/113.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        html = await self.fetch_url(url=url,params=None, headers=headers)
        if html:
            soup = BeautifulSoup(html, 'html5lib')
            result = soup.find_all(class_='result')
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
    return await BaiduNovels.start(novels_name)


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
    res = asyncio.get_event_loop().run_until_complete(start('intitle:雪中悍刀行 小说 阅读'))
    for i in res:
        print(i)
