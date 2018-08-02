# coding:utf-8

import random
import config
import asyncio
import aiohttp

from db.DataStore import sqlhelper

timeout = aiohttp.ClientTimeout(total=config.TIMEOUT)


class Html_Downloader:
    @staticmethod
    async def download(url,semphore, executor=None):
        loop = asyncio.get_event_loop()
        async with semphore:
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url=url, headers=config.get_header()) as response:
                        if response.reason != "OK" or len(await response.read()) < 500:
                            raise ConnectionError
                        else:
                            return await response.text()

            except Exception:   #如果抛出异常就使用代理下载
                count = 0  # 重试次数
                retry_time = config.RETRY_TIME
                select_num = retry_time * 5
                proxylist = await loop.run_in_executor(executor, sqlhelper.select, select_num)
                if not proxylist:
                    return None
                while count < retry_time:
                    try:
                        proxy = random.choice(proxylist)
                        ip = proxy[0]
                        port = proxy[1]
                        proxies = {"http": "http://%s:%s" % (ip, port), "https": "http://%s:%s" % (ip, port)}
                        async with aiohttp.ClientSession(timeout=timeout) as session:
                            proxy = proxies["http"] if url.split("://")[0] == "http" else proxies["https"]
                            async with session.get(url=url, headers=config.get_header(), proxy=proxy) as response:
                                if response.reason != "OK" or len(await response.read()) < 500:
                                    raise ConnectionError
                                else:
                                    return await response.text()
                    except Exception:
                        count += 1
        return None


if __name__ == '__main__':
    # loop = asyncio.get_event_loop()
    # res = loop.run_until_complete(Html_Downloader.download("http://www.baidu.com"))
    # print(res)
    pass
