#!/usr/bin/env python
"""
 Created by howie.hu at 2018/5/28.
"""

import os
import random

import aiofiles
import aiohttp
import arrow
import async_timeout
import cchardet
import charset_normalizer
import requests

from urllib.parse import urlparse

from tushu.config import LOGGER, CONFIG


async def _get_data(filename, default='') -> list:
    """
    Get data from a file
    :param filename: filename
    :param default: default value
    :return: data
    """
    root_folder = os.path.dirname(os.path.dirname(__file__))
    user_agents_file = os.path.join(
        os.path.join(root_folder, 'data'), filename)
    try:
        async with aiofiles.open(user_agents_file, mode='r') as f:
            data = [_.strip() for _ in await
            f.readlines()]
    except:
        data = [default]
    return data


async def get_random_user_agent() -> str:
    """
    Get a random user agent string.
    :return: Random user agent string.
    """
    return random.choice(await _get_data('user_agents.txt', CONFIG.USER_AGENT))


def get_time() -> str:
    utc = arrow.utcnow()
    local = utc.to(CONFIG.TIMEZONE)
    time = local.format("YYYY-MM-DD HH:mm:ss")
    return time


def get_netloc(url):
    """
    获取netloc
    :param url: 
    :return:  netloc
    """
    netloc = urlparse(url).netloc
    return netloc or None


async def target_fetch(url, headers, timeout=15):
    """
    :param url: target url
    :return: text
    """
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
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

def extract_base_url(url):
    parts = url.split('/')
    base_url = '/'.join(parts[:-1]) + '/'
    return base_url

async def target_fetch_by_list(url, headers, timeout=15):
    all_html = []
    page_index = 1
    if not url.endswith('1.html'):
        return all_html
    while True:
        base_url = extract_base_url(url)
        url = f"{base_url}{page_index}.html"
        try:
            # 发送 HTTP 请求获取网页内容
            response = requests.get(url, headers=headers, timeout=timeout)
            # 检查请求是否成功
            if response.status_code == 200:
                html = response.text
                all_html.append(html)
                page_index += 1
            else:
                print(f"Failed to fetch the page. Status code: {response.status_code}")
                break
        except Exception as e:
            print(f"An error occurred: {e}")
            break
    return all_html

def get_html_by_requests(url, headers, timeout=15):
    """
    :param url:
    :return:
    """
    try:
        if url.startswith('//') :
            url = 'https:' + url
        response = requests.get(url=url, headers=headers, verify=False, timeout=timeout)
        response.raise_for_status()
        content = response.content
        charset = cchardet.detect(content)
        text = content.decode(charset['encoding'])
        return text
    except Exception as e:
        LOGGER.exception(e)
        return None

def main():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    result = get_html_by_requests("https://book.qq.com/book-read/51651261/5",headers,15)
    print(result)


if __name__ == "__main__":
    main()