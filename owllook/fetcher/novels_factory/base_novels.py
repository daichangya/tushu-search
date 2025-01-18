#!/usr/bin/env python
"""
 Created by howie.hu at 2018/5/28.
"""
import aiohttp
import async_timeout
import requests
import charset_normalizer

from owllook.config import CONFIG, LOGGER, BLACK_DOMAIN, RULES, LATEST_RULES


class BaseNovels:
    """
    小说抓取父类
    """

    def __init__(self, logger=None):
        self.black_domain = BLACK_DOMAIN
        self.config = CONFIG
        self.latest_rules = LATEST_RULES
        self.logger = logger if logger else LOGGER
        self.rules = RULES

    async def fetch_url(self, url, params, headers):
        try:
            response = requests.get(url, params=params,headers=headers, timeout=10)
            response.raise_for_status()

            # 获取Content-Type并检查是否为HTML
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                raise Exception("搜索结果页面非HTML内容")

            # 使用charset-normalizer检测编码
            detected = charset_normalizer.from_bytes(response.content).best()
            encoding = detected.encoding if detected and detected.encoding else 'utf-8'

            # 使用检测到的编码解码内容
            text = response.content.decode(encoding, errors='replace')
            return text
        except requests.RequestException as e:
            raise Exception(f"请求百度失败：{e}")
        except Exception as e:
            raise Exception(f"解码百度搜索结果页面失败：{e}")

    @classmethod
    async def start(cls, novels_name):
        return await cls().novels_search(novels_name)

    async def data_extraction(self, html):
        """
        小说信息抓取函数
        :return:
        """
        raise NotImplementedError

    async def novels_search(self, novels_name):
        """
        小说搜索入口函数
        :return:
        """
        raise NotImplementedError
