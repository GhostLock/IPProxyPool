# coding:utf-8

import random
import config
import json
import asyncio
import aiohttp

import requests
import chardet

from db.DataStore import sqlhelper


class Html_Downloader(object):
    @staticmethod
    def download(url):
        try:
            r = requests.get(url=url, headers=config.get_header(), timeout=config.TIMEOUT)
            r.encoding = chardet.detect(r.content)['encoding']
            if (not r.ok) or len(r.content) < 500:
                raise ConnectionError
            else:
                return r.text

        except Exception:
            count = 0  # 重试次数
            proxylist = sqlhelper.select(10)
            if not proxylist:
                return None

            while count < config.RETRY_TIME:
                try:
                    proxy = random.choice(proxylist)
                    ip = proxy[0]
                    port = proxy[1]
                    proxies = {"http": "http://%s:%s" % (ip, port), "https": "http://%s:%s" % (ip, port)}

                    r = requests.get(url=url, headers=config.get_header(), timeout=config.TIMEOUT, proxies=proxies)
                    r.encoding = chardet.detect(r.content)['encoding']
                    if (not r.ok) or len(r.content) < 500:
                        raise ConnectionError
                    else:
                        return r.text
                except Exception:
                    count += 1

        return None

timeout = aiohttp.ClientTimeout(total=config.TIMEOUT)
loop = asyncio.get_event_loop()

class _Html_Downloader:
    @staticmethod
    async def download(url,executor=None):
        try:
            with aiohttp.ClientSession(timeout=timeout) as session:
                with session.get(url=url,headers=config.get_header()) as response:
                    if response.reason != "OK" or len(await response.read())<500 :   #TODO response.content 输出是什么？
                        raise ConnectionError
                    else:
                        return await response.text()

        except Exception:
            count = 0  # 重试次数
            retry_time = config.RETRY_TIME
            proxylist = await loop.run_in_executor(executor,sqlhelper.select,retry_time*5)
            if not proxylist:
                return None
            while count < retry_time:
                try:
                    proxy = random.choice(proxylist)
                    ip = proxy[0]
                    port = proxy[1]
                    proxies = {"http": "http://%s:%s" % (ip, port), "https": "http://%s:%s" % (ip, port)}
                    with aiohttp.ClientSession(timeout=timeout) as session:
                        #TODO 写到这里！！！！！！proxy=...
                        with session.get(url=url, headers=config.get_header(),proxy="httpx://xxxxxxx") as response:
                            if response.reason != "OK" or len(
                                    await response.read()) < 500:  # TODO response.content 输出是什么？
                                raise ConnectionError
                            else:
                                return await response.text()


                except Exception:
                    count += 1

        return None


if __name__ == '__main__':
    pass